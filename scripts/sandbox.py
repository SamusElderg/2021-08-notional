import json

import scripts.deploy_v1
from brownie import accounts
from brownie.network import web3
from scripts.config import CurrencyDefaults, nTokenDefaults
from scripts.deployment import TestEnvironment, TokenType
from tests.governance.test_governance import execute_proposal


def listCurrencyCalldata(symbol, v2env, **kwargs):
    buffer = kwargs["buffer"] if "buffer" in kwargs else CurrencyDefaults["buffer"]
    haircut = kwargs["haircut"] if "haircut" in kwargs else CurrencyDefaults["haircut"]
    liquidationDiscount = (
        kwargs["liquidationDiscount"]
        if "liquidationDiscount" in kwargs
        else CurrencyDefaults["liquidationDiscount"]
    )

    return web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="listCurrency",
        args=[
            (v2env.cToken[symbol].address, symbol == "USDT", TokenType["cToken"]),
            (v2env.token[symbol].address, symbol == "USDT", TokenType["UnderlyingToken"]),
            v2env.ethOracle[symbol].address,
            False,
            buffer,
            haircut,
            liquidationDiscount,
        ],
    )


def enableCashGroupCallData(currencyId, symbol, v2env, **kwargs):
    enable = web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="enableCashGroup",
        args=[
            currencyId,
            v2env.cTokenAggregator[symbol].address,
            (
                CurrencyDefaults["maxMarketIndex"],
                CurrencyDefaults["rateOracleTimeWindow"],
                CurrencyDefaults["totalFee"],
                CurrencyDefaults["reserveFeeShare"],
                CurrencyDefaults["debtBuffer"],
                CurrencyDefaults["fCashHaircut"],
                CurrencyDefaults["settlementPenalty"],
                CurrencyDefaults["liquidationfCashDiscount"],
                CurrencyDefaults["tokenHaircut"][0 : CurrencyDefaults["maxMarketIndex"]],
                CurrencyDefaults["rateScalar"][0 : CurrencyDefaults["maxMarketIndex"]],
            ),
            v2env.token[symbol].name() if symbol != "ETH" else "Ether",
            symbol,
        ],
    )

    deposit = web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="updateDepositParameters", args=[currencyId, *(nTokenDefaults["Deposit"])]
    )

    init = web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="updateInitializationParameters",
        args=[currencyId, *(nTokenDefaults["Initialization"])],
    )

    token = web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="updateTokenCollateralParameters",
        args=[currencyId, *(nTokenDefaults["Collateral"])],
    )

    incentiveRate = web3.eth.contract(abi=v2env.notional.abi).encodeABI(
        fn_name="updateIncentiveEmissionRate",
        args=[currencyId, CurrencyDefaults["incentiveEmissionRate"]],
    )

    return [enable, deposit, init, token, incentiveRate]


def initialize_v2env(v2env, migrator):
    v2env.noteERC20.delegate(v2env.multisig, {"from": v2env.multisig})
    # proposal to list currencies
    targets = [v2env.notional.address] * 4
    values = [0] * 4
    calldatas = [
        listCurrencyCalldata("DAI", v2env),
        listCurrencyCalldata("USDC", v2env),
        listCurrencyCalldata("USDT", v2env, haircut=0),
        listCurrencyCalldata("WBTC", v2env),
    ]
    execute_proposal(v2env, targets, values, calldatas)
    # TODO: deploy non mintable token

    # proposal to enable each cash group (wbtc left off to test no cash group and ntoken)
    for (currencyId, symbol) in [(2, "DAI"), (3, "USDC"), (4, "USDT")]:
        targets = [v2env.notional.address] * 5
        values = [0] * 5
        calldatas = enableCashGroupCallData(currencyId, symbol, v2env)
        execute_proposal(v2env, targets, values, calldatas)

    # Add global transfer operator
    targets = [v2env.notional.address]
    values = [0]
    calldatas = [
        web3.eth.contract(abi=v2env.notional.abi).encodeABI(
            fn_name="updateGlobalTransferOperator", args=[migrator.address, True]
        )
    ]
    execute_proposal(v2env, targets, values, calldatas)


def main():
    v2env = TestEnvironment(accounts[0], withGovernance=True, multisig=accounts[0])
    v1env = scripts.deploy_v1.deploy_v1(v2env)
    initialize_v2env(v2env, v1env["Migrator"])

    v1contractsFile = {
        "chainId": 1337,
        "networkName": "unknown",
        "deployer": accounts[9].address,
        "escrow": v1env["Escrow"].address,
        "portfolios": v1env["Portfolios"].address,
        "directory": v1env["Directory"].address,
        "erc1155": v1env["ERC1155Token"].address,
        "erc1155trade": v1env["ERC1155Trade"].address,
        "startBlock": 1,
    }

    v2contractsFile = {
        "chainId": 1337,
        "networkName": "unknown",
        "deployer": v2env.deployer.address,
        "notional": v2env.notional.address,
        "note": v2env.noteERC20.address,
        "governor": v2env.governor.address,
        "comptroller": v2env.comptroller.address,
        "startBlock": 1,
    }

    with open("sandbox2.local.json", "w") as f:
        json.dump(v1contractsFile, f, sort_keys=True, indent=4)

    with open("v2.local.json", "w") as f:
        json.dump(v2contractsFile, f, sort_keys=True, indent=4)

    with open("abi/AssetRateAggregator.json", "w") as f:
        json.dump(v2env.cTokenAggregator["ETH"].abi, f, sort_keys=True, indent=4)

    with open("abi/IAggregator.json", "w") as f:
        json.dump(v2env.ethOracle["DAI"].abi, f, sort_keys=True, indent=4)

    with open("abi/nTokenERC20.json", "w") as f:
        json.dump(v2env.nToken[1].abi, f, sort_keys=True, indent=4)

    with open("abi/Governor.json", "w") as f:
        json.dump(v2env.governor.abi, f, sort_keys=True, indent=4)

    with open("abi/NoteERC20.json", "w") as f:
        json.dump(v2env.noteERC20.abi, f, sort_keys=True, indent=4)

    with open("abi/Notional.json", "w") as f:
        json.dump(v2env.notional.abi, f, sort_keys=True, indent=4)
