import pytest
from tests.constants import SECONDS_IN_YEAR, START_TIME


@pytest.mark.balances
class TestIncentives:
    @pytest.fixture(scope="module", autouse=True)
    def incentives(self, MockIncentives, accounts):
        return MockIncentives.deploy({"from": accounts[0]})

    @pytest.fixture(autouse=True)
    def isolation(self, fn_isolation):
        pass

    def test_incentives_no_supply(self, incentives, accounts):
        # This case appears when minting the initial tokens
        incentives.setNTokenParameters(1, accounts[1], 0, 100)

        claimed = incentives.calculateIncentivesToClaim(
            accounts[1], 1_000_000e8, START_TIME, 0, START_TIME + SECONDS_IN_YEAR
        )

        assert claimed == 0

    def test_incentives_one_year(self, incentives, accounts):
        incentives.setNTokenParameters(1, accounts[1], 150_000_000e8, 100)

        claimed = incentives.calculateIncentivesToClaim(
            accounts[1], 1_000_000e8, START_TIME, 50_000_000, START_TIME + SECONDS_IN_YEAR
        )

        # After 1 year, 1% of the avg supply returns 1.5% of the tokens minted
        # (1% * 1.5 multiplier)
        assert claimed == 1.5e8

    def test_incentives_zero_time(self, incentives, accounts):
        incentives.setNTokenParameters(1, accounts[1], 150_000_000e8, 100)

        claimed = incentives.calculateIncentivesToClaim(
            accounts[1], 1_000_000e8, START_TIME, 50_000_000, START_TIME
        )

        assert claimed == 0

    def test_incentives_two_years(self, incentives, accounts):
        incentives.setNTokenParameters(1, accounts[1], 150_000_000e8, 100)

        claimed = incentives.calculateIncentivesToClaim(
            accounts[1], 1_000_000e8, START_TIME, 50_000_000, START_TIME + SECONDS_IN_YEAR * 2
        )

        # After 2 years, 1% of the avg supply returns 4% of the tokens minted
        # (1% * 2 * 2 multiplier)
        assert claimed == 4e8

    def test_incentives_three_years(self, incentives, accounts):
        incentives.setNTokenParameters(1, accounts[1], 150_000_000e8, 100)

        claimed = incentives.calculateIncentivesToClaim(
            accounts[1], 1_000_000e8, START_TIME, 50_000_000, START_TIME + SECONDS_IN_YEAR * 3
        )

        # After 3 years, 1% of the avg supply returns 6% of the tokens minted
        # (1% * 3 * 2 multiplier)
        # Tests that the multiplier does not increase to 2.5
        assert claimed == 6e8
