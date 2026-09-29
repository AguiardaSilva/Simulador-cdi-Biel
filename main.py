<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador CDI - Protótipo Arrancada 2T</title>
    <script src="https://jsdelivr.net"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: #0b0e14;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            width: 100vw;
            min-height: 100vh;
            overflow-y: auto;
            overflow-x: hidden;
            position: relative;
        }

        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url('https://unsplash.com');
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center center;
            background-attachment: fixed;
            z-index: 0;
            pointer-events: none;
        }

        body::after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(180deg, rgba(6, 8, 12, 0.75) 0%, rgba(6, 8, 12, 0.65) 50%, rgba(6, 8, 12, 0.8) 100%);
            z-index: 1;
            pointer-events: none;
        }

        .container {
            position: relative;
            z-index: 2;
            background: rgba(17, 22, 30, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(56, 139, 253, 0.2);
            border-radius: 20px;
            padding: 30px;
            width: 100%;
            max-width: 550px;
            margin: 20px auto;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(88, 166, 255, 0.05);
        }

        .container.with-charts {
            max-width: 900px;
        }

        @media (max-width: 480px) {
            .container {
                padding: 18px;
                border-radius: 12px;
                margin: 10px auto;
            }
            body::before {
                background-attachment: scroll;
            }
        }

        .charts-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-top: 25px;
        }

        @media (min-width: 760px) {
            .charts-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        .chart-panel {
            background: rgba(1, 4, 9, 0.7);
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #30363d;
        }

        .chart-panel h2 {
            margin-bottom: 10px;
        }

        .chart-wrapper {
            position: relative;
            width: 100%;
            height: 220px;
        }

        h1 {
            font-size: 1.6rem;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }

        h2 {
            font-size: 1.1rem;
            color: #f0883e;
            margin-bottom: 15px;
            text-transform: uppercase;
            border-left: 3px solid #f0883e;
            padding-left: 8px;
        }

        .panel {
            background: rgba(30, 37, 48, 0.5);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }

        .control-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            font-size: 0.9rem;
            margin-bottom: 8px;
            color: #8b949e;
        }

        .rpm-display {
            font-size: 2.4rem;
            font-weight: bold;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 12px;
            font-family: 'Courier New', Courier, monospace;
            text-shadow: 0 0 15px rgba(88, 166, 255, 0.2);
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #21262d;
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #58a6ff;
            cursor: pointer;
            box-shadow: 0 0 12px rgba(88, 166, 255, 0.6);
            transition: transform 0.1s;
        }

        input[type="range"]::-webkit-slider-thumb:active {
            transform: scale(1.2);
        }

        .auto-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }

        .input-field input {
            width: 100%;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px;
            color: #c9d1d9;
            text-align: center;
            font-size: 1rem;
            font-family: monospace;
        }

        .input-field input:focus {
            border-color: #58a6ff;
            outline: none;
        }

        .btn {
            width: 100%;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            transition: background 0.2s, transform 0.1s;
        }

        .btn:hover { background: #2ea043; }
        .btn:active { transform: scale(0.98); }
        .btn.stop { background: #da3633; }
        .btn.stop:hover { background: #f85149; }

        .results {
            background: rgba(1, 4, 9, 0.7);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #30363d;
        }

        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            font-size: 1rem;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .label { color: #8b949e; }
        .value {
            font-weight: bold;
            color: #f0883e;
            font-family: monospace;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-running { background: #238636; color: white; box-shadow: 0 0 10px rgba(35,134,54,0.4); }
        .status-limit { background: #da3633; color: white; box-shadow: 0 0 10px rgba(218,54,51,0.4); }
        .status-auto { background: #8957e5; color: white; box-shadow: 0 0 10px rgba(137,87,229,0.4); }

        .fuel-selector {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 8px;
        }

        @media (min-width: 480px) {
            .fuel-selector {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        .fuel-btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #8b949e;
            padding: 12px 8px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 0.85rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .fuel-btn span.icon {
            font-size: 1.3rem;
        }

        .fuel-btn:hover {
            border-color: #8b949e;
            color: #c9d1d9;
        }

        .fuel-btn.active[data-fuel="gasolina"] { background: rgba(240, 136, 62, 0.15); border-color: #f0883e; color: #f0883e; box-shadow: 0 0 12px rgba(240,136,62,0.2); }
        .fuel-btn.active[data-fuel="etanol"] { background: rgba(88, 166, 255, 0.15); border-color: #58a6ff; color: #58a6ff; box-shadow: 0 0 12px rgba(88,166,255,0.2); }
        .fuel-btn.active[data-fuel="metanol"] { background: rgba(53, 194, 91, 0.15); border-color: #35c25b; color: #35c25b; box-shadow: 0 0 12px rgba(53,194,91,0.2); }
        .fuel-btn.active[data-fuel="nitrometano"] { background: rgba(218, 54, 51, 0.15); border-color: #da3633; color: #da3633; box-shadow: 0 0 12px rgba(218,54,51,0.2); }
    </style>
</head>
<body>

    <div class="container with-charts">
        <h1>Biel CDI Drag-Sim</h1>
        
        <div class="panel">
            <h2>Combustível Alvo (Parâmetros 2T)</h2>
            <div class="fuel-selector">
                <button class="fuel-btn active" data-fuel="gasolina" onclick="selecionarCombustivel('gasolina')">
                    <span class="icon">⛽</span>
                    <span>Gasolina</span>
                </button>
                <button class="fuel-btn" data-fuel="etanol" onclick="selecionarCombustivel('etanol')">
                    <span class="icon">🌽</span>
                    <span>Etanol</span>
                </button>
                <button class="fuel-btn" data-fuel="metanol" onclick="selecionarCombustivel('metanol')">
