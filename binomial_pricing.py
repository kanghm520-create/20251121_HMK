"""
Binomial option pricing model implementation.

This module provides a function for pricing European and American call/put options
using the Cox-Ross-Rubinstein binomial tree.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

OptionType = Literal["call", "put"]


@dataclass
class BinomialParameters:
    """Configuration for the binomial pricing tree.

    Attributes:
        spot: Current spot price of the underlying asset.
        strike: Option strike price.
        maturity: Time to maturity in years.
        rate: Risk-free interest rate expressed as a yearly decimal.
        volatility: Annualized volatility of the underlying asset.
        steps: Number of time steps in the binomial tree (must be positive).
        dividend_yield: Continuous dividend yield (yearly decimal). Defaults to 0.0.
        option_type: "call" or "put". Defaults to "call".
        american: Whether to allow early exercise (American option). Defaults to False.
    """

    spot: float
    strike: float
    maturity: float
    rate: float
    volatility: float
    steps: int
    dividend_yield: float = 0.0
    option_type: OptionType = "call"
    american: bool = False


class InvalidParameterError(ValueError):
    """Raised when a provided parameter is not valid for the binomial model."""


def _validate_parameters(params: BinomialParameters) -> None:
    if params.spot <= 0:
        raise InvalidParameterError("Spot price must be positive.")
    if params.strike <= 0:
        raise InvalidParameterError("Strike price must be positive.")
    if params.maturity <= 0:
        raise InvalidParameterError("Maturity must be positive.")
    if params.volatility <= 0:
        raise InvalidParameterError("Volatility must be positive.")
    if params.steps <= 0:
        raise InvalidParameterError("Steps must be a positive integer.")
    if params.option_type not in ("call", "put"):
        raise InvalidParameterError("Option type must be either 'call' or 'put'.")


def price_option(params: BinomialParameters) -> float:
    """Price an option using the Cox-Ross-Rubinstein binomial model.

    Args:
        params: :class:`BinomialParameters` containing model inputs.

    Returns:
        The present value of the option.

    Raises:
        InvalidParameterError: If the input parameters are invalid or produce
            an invalid risk-neutral probability.
    """

    _validate_parameters(params)

    dt = params.maturity / params.steps
    up = math.exp(params.volatility * math.sqrt(dt))
    down = 1 / up
    discount = math.exp(-params.rate * dt)

    growth = math.exp((params.rate - params.dividend_yield) * dt)
    probability = (growth - down) / (up - down)

    if not 0 <= probability <= 1:
        raise InvalidParameterError(
            "Risk-neutral probability is not between 0 and 1. Check inputs for dt or volatility."
        )

    # Underlying prices at maturity
    asset_prices = [
        params.spot * (up ** j) * (down ** (params.steps - j))
        for j in range(params.steps + 1)
    ]

    def payoff(price: float) -> float:
        if params.option_type == "call":
            return max(price - params.strike, 0.0)
        return max(params.strike - price, 0.0)

    option_values = [payoff(price) for price in asset_prices]

    # Backward induction through the tree
    for step in range(params.steps - 1, -1, -1):
        for i in range(step + 1):
            continuation = discount * (
                probability * option_values[i + 1]
                + (1 - probability) * option_values[i]
            )
            if params.american:
                underlying_price = params.spot * (up ** i) * (down ** (step - i))
                option_values[i] = max(continuation, payoff(underlying_price))
            else:
                option_values[i] = continuation

    return option_values[0]


def price_option_simplified(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    steps: int,
    option_type: OptionType = "call",
    american: bool = False,
    dividend_yield: float = 0.0,
) -> float:
    """Convenience wrapper around :func:`price_option`.

    Accepts individual arguments instead of a dataclass and forwards them to
    the core pricing function.
    """

    return price_option(
        BinomialParameters(
            spot=spot,
            strike=strike,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
            steps=steps,
            dividend_yield=dividend_yield,
            option_type=option_type,
            american=american,
        )
    )


if __name__ == "__main__":
    sample_params = BinomialParameters(
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
        steps=100,
        option_type="call",
        american=False,
    )

    european_price = price_option(sample_params)
    american_price = price_option_simplified(
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
        steps=100,
        option_type="call",
        american=True,
    )

    print(f"European call price: {european_price:.4f}")
    print(f"American call price:  {american_price:.4f}")
