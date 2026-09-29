from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# CONFIGURAÇÕES REPLICADAS DO ESP32
DWELL_US = 3000
MAX_RPM = 11000

# MAPA DE AVANÇO ORIGINAL
rpmMap = [1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000]
advanceMap = [12.0, 18.0, 22.0, 25.0, 26.0, 25.0, 20.0, 16.0]

def get_advance_from_map(rpm):
    if rpm <= rpmMap[0]:
        return advanceMap[0]
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]
        
    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i+1]:
            # Interpolação linear idêntica ao C++
            ratio = (rpm - rpmMap[i]) / (rpmMap[i+1] - rpmMap[i])
            return advanceMap[i] + ratio * (advanceMap[i+1] - advanceMap[i])
    return advanceMap[0]

@app.route('/simular', methods=['GET'])
def simular_ignicao():
    # Obtém o RPM enviado pela URL (Ex: /simular?rpm=3500)
    rpm = request.args.get('rpm', default=1000, type=int)
    kill_switch = request.args.get('kill', default='false', type=str).lower() == 'true'

    if kill_switch:
        return jsonify({"status": "CORTE ATIVADO", "ignicao": False, "motivo": "Kill Switch Pressionado"})

    if rpm >= MAX_RPM:
        return jsonify({"status": "LIMITADOR ATIVO", "ignicao": False, "rpm": rpm, "motivo": "Giro Máximo Excedido"})

    # Calcula tempo de 1 volta em microssegundos (60M / RPM)
    periodo_us = 60000000 / rpm if rpm > 0 else 0
    avanco_graus = get_advance_from_map(rpm)
    
    # Conversão de graus para tempo
    avanco_us = (avanco_graus / 360.0) * periodo_us
    atraso_centelha_us = periodo_us - avanco_us

    # Trava de segurança física do ESP32
    if atraso_centelha_us < 80:
        atraso_centelha_us = 80

    return jsonify({
        "status": "MOTOR RODANDO",
        "ignicao": True,
        "rpm_atual": rpm,
        "avanco_calculado_graus": round(avanco_graus, 2),
        "tempo_de_uma_volta_us": round(periodo_us, 0),
        "tempo_espera_ignicao_us": round(atraso_centelha_us, 0),
        "tempo_carga_bobina_dwell_us": DWELL_US
    })

if __name__ == '__main__':
    # O Railway exige ler a porta dinâmica do ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
