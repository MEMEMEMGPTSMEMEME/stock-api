from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# 유효한 폴더 이름 목록
DATA_SOURCES = {
    "market": "market_data",
    "momentum": "Momentum_stock_date"
}

@app.route("/price", methods=["GET"])
def get_price():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "daily")
    source = request.args.get("source", "market")  # 기본값은 market_data

    if source not in DATA_SOURCES:
        return jsonify({"error": f"Invalid source '{source}'"}), 400

    data_dir = DATA_SOURCES[source]
    path = os.path.join(data_dir, f"{symbol}_{interval}.csv")

    if not os.path.exists(path):
        return jsonify({"error": "CSV not found"}), 404

    df = pd.read_csv(path)
    latest = df.iloc[-1].to_dict()
    return jsonify({
        "symbol": symbol,
        "source": source,
        "interval": interval,
        "latest": latest
    })

@app.route("/avg", methods=["GET"])
def get_avg_close():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "daily")
    days = int(request.args.get("days", 5))
    source = request.args.get("source", "market")

    if source not in DATA_SOURCES:
        return jsonify({"error": f"Invalid source '{source}'"}), 400

    data_dir = DATA_SOURCES[source]
    path = os.path.join(data_dir, f"{symbol}_{interval}.csv")

    if not os.path.exists(path):
        return jsonify({"error": "CSV not found"}), 404

    df = pd.read_csv(path)
    avg = df.tail(days)["Close"].mean()
    return jsonify({
        "symbol": symbol,
        "source": source,
        "interval": interval,
        "days": days,
        "average_close": round(avg, 3)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)