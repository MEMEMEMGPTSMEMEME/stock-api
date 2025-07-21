from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# 유효한 폴더 이름 목록
DATA_SOURCES = {
    "market": "market_data",
    "momentum": "Momentum_stock_date"
}

def load_data(symbol, interval, source):
    if source not in DATA_SOURCES:
        return None, f"Invalid source '{source}'"
    path = os.path.join(DATA_SOURCES[source], f"{symbol}_{interval}.csv")
    if not os.path.exists(path):
        return None, "CSV not found"
    df = pd.read_csv(path)
    return df, None

@app.route("/")
def index():
    return "Stock API is running.", 200

@app.route("/price", methods=["GET"])
def get_price():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "daily")
    source = request.args.get("source", "market")

    df, error = load_data(symbol, interval, source)
    if error:
        return jsonify({"error": error}), 400

    latest = df.iloc[-1].to_dict()
    return jsonify({"symbol": symbol, "source": source, "interval": interval, "latest": latest})

@app.route("/avg", methods=["GET"])
def get_avg_close():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "daily")
    days = int(request.args.get("days", 5))
    source = request.args.get("source", "market")

    df, error = load_data(symbol, interval, source)
    if error:
        return jsonify({"error": error}), 400

    avg = df.tail(days)["Close"].mean()
    return jsonify({"symbol": symbol, "source": source, "interval": interval, "days": days, "average_close": round(avg, 3)})

@app.route("/similarity", methods=["GET"])
def get_similarity():
    base = request.args.get("base")
    target = request.args.get("target")
    interval = request.args.get("interval", "daily")
    source = request.args.get("source", "market")

    df1, err1 = load_data(base, interval, source)
    df2, err2 = load_data(target, interval, source)
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400

    merged = pd.merge(df1, df2, on="Date", suffixes=("_base", "_target"))
    corr = merged["Close_base"].corr(merged["Close_target"])
    return jsonify({"base": base, "target": target, "interval": interval, "source": source, "correlation": round(corr, 4), "days_compared": len(merged)})

@app.route("/pattern/surge", methods=["GET"])
def surge_pattern():
    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "daily")
    threshold = float(request.args.get("threshold", 0.1))
    source = request.args.get("source", "market")

    df, error = load_data(symbol, interval, source)
    if error:
        return jsonify({"error": error}), 400

    df["Return"] = df["Close"].pct_change()
    df["Surge"] = df["Return"] > threshold
    surges = df[df["Surge"]].to_dict(orient="records")
    return jsonify({"symbol": symbol, "surges": surges})

@app.route("/pattern/surge/similarity", methods=["GET"])
def surge_similarity():
    base = request.args.get("base")
    target = request.args.get("target")
    interval = request.args.get("interval", "daily")
    source = request.args.get("source", "market")

    df1, err1 = load_data(base, interval, source)
    df2, err2 = load_data(target, interval, source)
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400

    df1["Surge"] = df1["Close"].pct_change() > 0.1
    df2["Surge"] = df2["Close"].pct_change() > 0.1
    merged = pd.merge(df1[["Date", "Surge"]], df2[["Date", "Surge"]], on="Date", suffixes=("_base", "_target"))
    similarity = (merged["Surge_base"] == merged["Surge_target"]).mean()
    return jsonify({"base": base, "target": target, "similarity": round(similarity, 4), "days": len(merged)})

@app.route("/leadlag", methods=["GET"])
def lead_lag():
    base = request.args.get("base")
    target = request.args.get("target")
    interval = request.args.get("interval", "daily")
    lag = int(request.args.get("lag", 1))
    source = request.args.get("source", "market")

    df1, err1 = load_data(base, interval, source)
    df2, err2 = load_data(target, interval, source)
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400

    merged = pd.merge(df1[["Date", "Close"]], df2[["Date", "Close"]], on="Date", suffixes=("_base", "_target"))
    merged["Close_base_shifted"] = merged["Close_base"].shift(lag)
    corr = merged["Close_base_shifted"].corr(merged["Close_target"])
    return jsonify({"base": base, "target": target, "lag": lag, "correlation": round(corr, 4)})

@app.route("/coupling", methods=["GET"])
def coupling():
    base = request.args.get("base")
    target = request.args.get("target")
    interval = request.args.get("interval", "daily")
    source = request.args.get("source", "market")

    df1, err1 = load_data(base, interval, source)
    df2, err2 = load_data(target, interval, source)
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400

    df1["Return"] = df1["Close"].pct_change()
    df2["Return"] = df2["Close"].pct_change()
    merged = pd.merge(df1[["Date", "Return"]], df2[["Date", "Return"]], on="Date", suffixes=("_base", "_target"))
    decoupled = (merged["Return_base"] * merged["Return_target"] < 0).mean()
    return jsonify({"base": base, "target": target, "decoupled_rate": round(decoupled, 4), "days": len(merged)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
