"""Simple Flask web server for Monte Carlo option pricing."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Tuple

from flask import Flask, jsonify, render_template_string, request, url_for

from monte_carlo_pricing import (
    InvalidMonteCarloParameterError,
    InvalidPayoffError,
    MonteCarloParameters,
    build_payoff_function,
    price_option_monte_carlo,
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

_FORM_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Monte Carlo Option Pricer</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 720px; line-height: 1.5; }
    label { display: block; margin-top: 0.5rem; }
    input { width: 100%; padding: 0.4rem; margin-top: 0.2rem; box-sizing: border-box; }
    .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }
    .error { color: #b30000; background: #ffe0e0; padding: 0.5rem; border-radius: 4px; }
    .result { color: #0b650b; background: #e4ffe4; padding: 0.5rem; border-radius: 4px; font-weight: bold; }
    button { padding: 0.6rem 1rem; margin-top: 1rem; }
    code { background: #f2f2f2; padding: 0.1rem 0.2rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Monte Carlo Option Pricer</h1>
  <p>Provide the inputs below to estimate an option price. Payoffs use <code>S</code> for the terminal price (example: <code>max(S - 100, 0)</code> for a call).</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  {% if price is not none %}<div class="result">Estimated price: {{ price }}</div>{% endif %}
  <form method="post">
    <div class="row">
      <label>Spot price
        <input name="spot" type="number" step="any" value="{{ form.spot }}" required>
      </label>
      <label>Maturity (years)
        <input name="maturity" type="number" step="any" value="{{ form.maturity }}" required>
      </label>
      <label>Risk-free rate
        <input name="rate" type="number" step="any" value="{{ form.rate }}" required>
      </label>
      <label>Volatility
        <input name="volatility" type="number" step="any" value="{{ form.volatility }}" required>
      </label>
      <label>Simulations
        <input name="simulations" type="number" step="1" min="1" value="{{ form.simulations }}" required>
      </label>
      <label>Random seed (optional)
        <input name="seed" type="number" step="1" value="{{ form.seed }}">
      </label>
    </div>
    <label>Payoff expression
      <input name="payoff" type="text" value="{{ form.payoff }}" required>
    </label>
    <button type="submit">Price option</button>
  </form>
  <h2>API usage</h2>
  <p>POST JSON to <code>{{ url_for('price_api', _external=False) }}</code> with the fields shown above to receive <code>{"price": value}</code> or an error message.</p>
</body>
</html>
"""


def _extract_parameters(
    source: Dict[str, Any]
) -> Tuple[MonteCarloParameters, str, Callable[[float], float]]:
    payoff_expr = str(source.get("payoff", "max(S - 100, 0)") or "max(S - 100, 0)")
    try:
        payoff_fn = build_payoff_function(payoff_expr)
    except InvalidPayoffError as exc:
        raise InvalidPayoffError(str(exc)) from exc

    try:
        params = MonteCarloParameters(
            spot=float(source.get("spot", 100.0)),
            maturity=float(source.get("maturity", 1.0)),
            rate=float(source.get("rate", 0.05)),
            volatility=float(source.get("volatility", 0.2)),
            simulations=int(source.get("simulations", 100000)),
            seed=int(source["seed"]) if source.get("seed") not in (None, "") else None,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidMonteCarloParameterError("Inputs must be numeric.") from exc

    return params, payoff_expr, payoff_fn


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    price = None
    form_data: Dict[str, Any] = {
        "spot": request.form.get("spot", 100.0),
        "maturity": request.form.get("maturity", 1.0),
        "rate": request.form.get("rate", 0.05),
        "volatility": request.form.get("volatility", 0.2),
        "simulations": request.form.get("simulations", 100000),
        "seed": request.form.get("seed", ""),
        "payoff": request.form.get("payoff", "max(S - 100, 0)"),
    }

    if request.method == "POST":
        try:
            params, payoff_expr, payoff_fn = _extract_parameters(request.form)
            result = price_option_monte_carlo(params, payoff_fn)
            price = f"{result:.4f}"
            app.logger.info("Priced payoff '%s' at %.6f", payoff_expr, result)
        except (InvalidPayoffError, InvalidMonteCarloParameterError) as exc:
            error = str(exc)

    return render_template_string(_FORM_TEMPLATE, price=price, error=error, form=form_data)


@app.route("/api/price", methods=["POST"])
def price_api():
    if not request.is_json:
        return jsonify({"error": "Send JSON payload."}), 400

    try:
        params, _, payoff_fn = _extract_parameters(request.json)
        price = price_option_monte_carlo(params, payoff_fn)
    except (InvalidPayoffError, InvalidMonteCarloParameterError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"price": price})


def main() -> None:
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == "__main__":
    main()
