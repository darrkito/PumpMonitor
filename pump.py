import streamlit as st
import asyncio
import websockets
import json
import base64
import queue
import threading
import time

# --- Configuración del estado de sesión ---
if 'buy_queue' not in st.session_state:
    st.session_state.buy_queue = queue.Queue()
    st.session_state.websocket_thread = None
    st.session_state.websocket_initialized = False # Nueva bandera para controlar la inicialización
    st.session_state.last_message = ""
    st.session_state.show_gif = False
    st.session_state.audio_played = False
    st.session_state.last_buy_time = 0

# --- Lógica del WebSocket en un hilo ---
def run_websocket_sync(buy_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def subscribe():
        uri = "wss://pumpportal.fun/api/data?api-key=enwn0wthcn46rxvmax86ce2t69150waudtm50du49x2mjruh61n3jrv8a9d36h2ced76px9tcxc7atjqc5uk0uumdx3kjgk9ddb54nhm85p74c3kd1wp4atqen36pvagc50pyc2ja4ykudmt7jp1n717n6ya26xkq6tkger9cwk8vu2ecwmpgj69tq7apb1dmr74vunc9kkuf8"
        try:
            async with websockets.connect(uri) as websocket:
                payload = {
                    "method": "subscribeTokenTrade",
                    "keys": ["BS7HxRitaY5ipGfbek1nmatWLbaS9yoWRSEQzCb3pump"]
                }
                await websocket.send(json.dumps(payload))
                print("Conexión WebSocket establecida. Esperando compras...")

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get('txType') == 'buy':
                        buy_queue.put(data)
                        print(f"Compra detectada y añadida a la cola: {data['traderPublicKey']}")

        except Exception as e:
            print(f"Error en la conexión WebSocket: {e}")

    loop.run_until_complete(subscribe())

# Iniciar el hilo del WebSocket solo si no está ya en ejecución.
if not st.session_state.websocket_initialized:
    st.session_state.websocket_thread = threading.Thread(
        target=run_websocket_sync, args=(st.session_state.buy_queue,), daemon=True
    )
    st.session_state.websocket_thread.start()
    st.session_state.websocket_initialized = True # Marcar como inicializado

# --- Interfaz de Streamlit ---
st.set_page_config(page_title="Monitor de Compras de Tokens", layout="wide")

# CSS para hacer el fondo totalmente transparente y ocultar la UI de Streamlit
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
    
    .stApp {
        background-color: transparent;
    }
    .main > div {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    header {
        visibility: hidden;
    }
    .st-emotion-cache-1c5c16 {
        visibility: hidden;
    }
    .st-emotion-cache-1c5c16::before {
        visibility: hidden;
    }
    .big-white-text {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 300%;
        color: white;
        background-color: transparent;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

placeholder = st.empty()

def play_audio():
    try:
        with open("Sound.mp3", "rb") as f:
            data = f.read()
        audio_base64 = base64.b64encode(data).decode("utf-8")
        audio_html = f"""
        <audio autoplay controls style="display:none;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Error: El archivo de audio 'Sound.mp3' no se encontró.")

# --- Lógica de procesamiento de la cola y visualización ---
try:
    data = st.session_state.buy_queue.get_nowait()
    st.session_state.last_message = f"¡Compra detectada! Trader: {data['traderPublicKey'][-4:]} compró {data['tokenAmount']:.2f} $DOGGY {data['solAmount']:.2f} SOL."
    st.session_state.show_gif = True
    st.session_state.last_buy_time = time.time()
    st.session_state.audio_played = False

except queue.Empty:
    # Si la cola está vacía, no hacemos nada.
    pass

# Lógica para controlar la visualización del video y el mensaje.
if st.session_state.show_gif:
    with placeholder.container():
        play_audio()
        # Se ha configurado el video para que se reproduzca automáticamente y en bucle
        st.image("lolxd.gif", width='content')
        st.write(f'<p class="big-white-text">{st.session_state.last_message}</p>', unsafe_allow_html=True)
        st.session_state.audio_played = True

    if time.time() - st.session_state.last_buy_time > 4:
        st.session_state.show_gif = False
        st.session_state.audio_played = False
        st.session_state.last_message = ""

else:
    pass

time.sleep(1)
st.rerun()
