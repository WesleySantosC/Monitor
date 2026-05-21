import requests
import time
import datetime
import os

from dotenv import load_dotenv

load_dotenv()

#if you wish array
#urls = [
#    os.getenv("URL"),
#    os.getenv("URL_TWO")
#]

URL = os.getenv("URL")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

REQUEST_TIMEOUT = 5
MONITOR_INTERVAL = 5

#Control status changes
lastStatus = None


def returnDescription(statusCode):
    match statusCode:

        case 200:
            return "Servidor online"

        case 400:
            return "Requisição inválida"

        case 401:
            return "Não autorizado"

        case 403:
            return "Acesso proibido"

        case 404:
            return "Página não encontrada"

        case 408:
            return "Timeout da requisição"

        case 429:
            return "Muitas requisições"

        case 500:
            return "Erro interno do servidor"

        case 502:
            return "Bad Gateway"

        case 503:
            return "Serviço indisponível"

        case 504:
            return "Gateway Timeout"

        case _:
            return f"Status desconhecido: {statusCode}"

def postSlackPayload(webhookSlack, payloadSlack):

    try:
        response = requests.post(
            webhookSlack,
            json=payloadSlack,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:

            print("\n❌ Error sending message to Slack")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as error:

        print("\n❌ Slack Webhook Error")
        print(error)

def buildSlackPayload(
    url,
    statusCode=None,
    description=None,
    latency=None,
    error=None
):

    timestamp = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if error:
        return {
            "text": (
                f"🚨 *Service Monitoring*\n\n"
                f"🌐 *URL:* {url}\n"
                f"❌ *Error:* {error}\n"
                f"🕒 *Timestamp:* {timestamp}"
            )
        }

    statusEmoji = "🟢" if 200 <= statusCode < 300 else "🔴"

    return {
        "text": (
            f"📡 *Service Monitoring*\n\n"
            f"🌐 *URL:* {url}\n"
            f"{statusEmoji} *HTTP Status:* {statusCode}\n"
            f"📝 *Message:* {description}\n"
            f"⚡ *Latency:* {round(latency * 1000, 3)} ms\n"
            f"🕒 *Timestamp:* {timestamp}"
        )
    }

def isActive(url):

    global lastStatus

    try:

        startTime = time.time()

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        latency = time.time() - startTime

        statusCode = response.status_code

        description = returnDescription(statusCode)

        if 200 <= statusCode < 300:
            currentStatus = "ONLINE"
        else:
            currentStatus = "OFFLINE"

        if lastStatus != currentStatus:

            payloadSlack = buildSlackPayload(
                url=url,
                statusCode=statusCode,
                description=description,
                latency=latency
            )

            postSlackPayload(
                SLACK_WEBHOOK,
                payloadSlack
            )

            if currentStatus == "ONLINE":
                print("\n🟢 Status changed to ONLINE")
            else:
                print("\n🔴 Status changed to OFFLINE")

        lastStatus = currentStatus

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{url} | "
            f"{statusCode} | "
            f"{round(latency * 1000, 3)} ms"
        )

    except requests.exceptions.ReadTimeout:

        currentStatus = "OFFLINE"

        if lastStatus != currentStatus:

            payloadSlack = buildSlackPayload(
                url=url,
                error="Timeout"
            )

            postSlackPayload(
                SLACK_WEBHOOK,
                payloadSlack
            )

            print("\n🔴 Status changed to OFFLINE")

        lastStatus = currentStatus

        print(f"\n⏰ Timeout: {url}")

    except requests.exceptions.ConnectionError:

        currentStatus = "OFFLINE"

        if lastStatus != currentStatus:

            payloadSlack = buildSlackPayload(
                url=url,
                error="Connection Error"
            )

            postSlackPayload(
                SLACK_WEBHOOK,
                payloadSlack
            )

            print("\n🔴 Status changed to OFFLINE")

        lastStatus = currentStatus

        print(f"\n🔌 Connection Error: {url}")

    except requests.exceptions.RequestException as error:

        currentStatus = "OFFLINE"

        if lastStatus != currentStatus:

            payloadSlack = buildSlackPayload(
                url=url,
                error=str(error)
            )

            postSlackPayload(
                SLACK_WEBHOOK,
                payloadSlack
            )

            print("\n🔴 Status changed to OFFLINE")

        lastStatus = currentStatus

        print(f"\n❌ Request Error: {error}")

if not URL:

    raise Exception("URL not defined in .env")

if not SLACK_WEBHOOK:

    raise Exception("SLACK_WEBHOOK not defined in .env")

while True:

    #Case array, utility for:
    #for url in urls:
    #    isActive(url)

    isActive(URL)

    time.sleep(MONITOR_INTERVAL)