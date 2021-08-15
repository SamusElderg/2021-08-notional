// SPDX-License-Identifier: GPL-3.0-only
pragma solidity >0.7.0;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// Mock decentralized exchange for testing liquidations
contract MockExchange {
    uint256 public exchangeRate;

    function setExchangeRate(uint256 exchangeRate_) external {
        exchangeRate = exchangeRate_;
    }

    function exchange(
        address assetIn,
        address assetOut,
        uint256 amountIn
    ) external {
        uint256 amountOut = (amountIn * exchangeRate) / 1e18;
        IERC20(assetIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(assetOut).transfer(msg.sender, amountOut);
    }
}
