"""
Monte Carlo option pricing with user-defined payoff expressions.

This module simulates terminal prices under a geometric Brownian motion and
computes the discounted expected payoff. Users can supply a custom payoff as a
Python expression involving the terminal price symbol ``S`` (for example,
``max(S - 100, 0)`` for a vanilla call).
"""
from __future__ import annotations

import ast
import math
import random
from dataclasses import dataclass
from typing import Callable, Mapping


class InvalidPayoffError(ValueError):
    """Raised when a provided payoff expression is not considered safe."""


class InvalidMonteCarloParameterError(ValueError):
    """Raised when Monte Carlo parameters are invalid."""


@dataclass
class MonteCarloParameters:
    """Inputs for the Monte Carlo pricing routine.

    Attributes:
        spot: Current price of the underlying asset.
        maturity: Time to maturity in years.
        rate: Risk-free interest rate expressed as a yearly decimal.
        volatility: Annualized volatility of the underlying asset.
        simulations: Number of simulated paths. Higher values increase accuracy.
        seed: Optional seed for reproducibility.
    """

    spot: float
    maturity: float
    rate: float
    volatility: float
    simulations: int = 100_000
    seed: int | None = None


_ALLOWED_NAMES: Mapping[str, object] = {
    "max": max,
    "min": min,
    "abs": abs,
    "math": math,
}

_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.FloorDiv,
    ast.LShift,
    ast.RShift,
    ast.BitOr,
    ast.BitAnd,
    ast.BitXor,
    ast.Compare,
    ast.Gt,
    ast.GtE,
    ast.Lt,
    ast.LtE,
    ast.Eq,
    ast.NotEq,
    ast.IfExp,
)


def _validate_monte_carlo_parameters(params: MonteCarloParameters) -> None:
    if params.spot <= 0:
        raise InvalidMonteCarloParameterError("Spot price must be positive.")
    if params.maturity <= 0:
        raise InvalidMonteCarloParameterError("Maturity must be positive.")
    if params.volatility <= 0:
        raise InvalidMonteCarloParameterError("Volatility must be positive.")
    if params.simulations <= 0:
        raise InvalidMonteCarloParameterError("Number of simulations must be positive.")


class _SafeExpressionValidator(ast.NodeVisitor):
    """AST visitor to ensure the payoff expression only uses safe constructs."""

    def visit(self, node):  # type: ignore[override]
        if not isinstance(node, _ALLOWED_NODES):
            raise InvalidPayoffError(
                f"Unsafe expression component: {node.__class__.__name__}."
            )
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_NAMES:
            raise InvalidPayoffError("Only simple function calls like max/min/abs are allowed.")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if node.id not in _ALLOWED_NAMES and node.id != "S":
            raise InvalidPayoffError(f"Unknown identifier '{node.id}'. Use 'S' for price.")



def build_payoff_function(expression: str) -> Callable[[float], float]:
    """Compile a payoff expression into a callable.

    The expression may reference the terminal price as ``S`` and the functions
    ``max``, ``min``, ``abs``, and the ``math`` module.
    """

    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - thin wrapper
        raise InvalidPayoffError("Payoff expression could not be parsed.") from exc

    _SafeExpressionValidator().visit(parsed)
    compiled = compile(parsed, "<payoff>", "eval")

    def payoff(price: float) -> float:
        local_scope = {"S": price}
        return float(eval(compiled, {"__builtins__": {}}, {**_ALLOWED_NAMES, **local_scope}))

    return payoff


def price_option_monte_carlo(
    params: MonteCarloParameters, payoff: Callable[[float], float]
) -> float:
    """Price an option using a Monte Carlo simulation of terminal prices."""

    _validate_monte_carlo_parameters(params)

    rng = random.Random(params.seed)
    drift = (params.rate - 0.5 * params.volatility**2) * params.maturity
    diffusion = params.volatility * math.sqrt(params.maturity)

    payoff_sum = 0.0
    for _ in range(params.simulations):
        z = rng.normalvariate(0.0, 1.0)
        terminal_price = params.spot * math.exp(drift + diffusion * z)
        payoff_sum += payoff(terminal_price)

    discounted_average = payoff_sum / params.simulations
    return math.exp(-params.rate * params.maturity) * discounted_average


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Monte Carlo option pricing with a custom payoff expression.",
    )
    parser.add_argument("--spot", type=float, default=100.0, help="Current spot price")
    parser.add_argument(
        "--maturity",
        type=float,
        default=1.0,
        help="Time to maturity in years (e.g., 0.5 for six months)",
    )
    parser.add_argument(
        "--rate", type=float, default=0.05, help="Risk-free annual interest rate"
    )
    parser.add_argument(
        "--volatility", type=float, default=0.2, help="Annualized volatility"
    )
    parser.add_argument(
        "--simulations",
        type=int,
        default=100_000,
        help="Number of Monte Carlo paths",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible results",
    )
    parser.add_argument(
        "--payoff",
        type=str,
        default="max(S - 100, 0)",
        help="Python expression for the payoff using 'S' as the terminal price",
    )

    args = parser.parse_args()

    payoff_fn = build_payoff_function(args.payoff)
    params = MonteCarloParameters(
        spot=args.spot,
        maturity=args.maturity,
        rate=args.rate,
        volatility=args.volatility,
        simulations=args.simulations,
        seed=args.seed,
    )

    price = price_option_monte_carlo(params, payoff_fn)
    print(
        "Input payoff: {}\nEstimated option price: {:.4f}".format(
            args.payoff, price
        )
    )
