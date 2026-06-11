import pygame
import threading
import textwrap
import queue
from datetime import datetime
from modules.settings.settings import TELEGRAM_ENABLED

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from modules.settings.settings import MY_MODEL
import subprocess

# ==========================================================
# OLLAMA CONFIG
# ==========================================================

MODEL = MY_MODEL

llm = ChatOllama(
    model=MODEL,
    temperature=0.7,
    stream=True,
)

# ==========================================================
# WINDOW CONFIG
# ==========================================================

WIDTH = 1280
HEIGHT = 900
FPS = 60

# ==========================================================
# COLORS
# ==========================================================

BG = (12, 14, 18)
CHAT_BG = (18, 20, 26)
INPUT_BG = (28, 31, 40)

USER_COLOR = (120, 190, 255)
AI_COLOR = (120, 255, 180)
SYSTEM_COLOR = (255, 210, 120)

TEXT = (235, 235, 235)
TIMESTAMP = (140, 140, 140)

# ==========================================================
# PYGAME INIT
# ==========================================================

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Ollama Desktop")

clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 24)
small_font = pygame.font.SysFont("consolas", 18)
tiny_font = pygame.font.SysFont("consolas", 14)

# ==========================================================
# STATE
# ==========================================================

messages = []
conversation = [
    #SystemMessage(
    #    content="You are a helpful assistant."
    #)
]

input_text = ""

waiting = False
auto_scroll = True

scroll_offset = 0
max_scroll = 0

stream_queue = queue.Queue()

# ==========================================================
# HELPERS
# ==========================================================

def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def add_message(role, content):
    messages.append({
        "role": role,
        "content": content,
        "timestamp": timestamp()
    })


def role_color(role):
    if role == "user":
        return USER_COLOR
    if role == "assistant":
        return AI_COLOR
    return SYSTEM_COLOR


# ==========================================================
# OLLAMA THREAD
# ==========================================================

def ask_ollama(prompt):

    global waiting

    try:

        conversation.append(
            HumanMessage(content=prompt)
        )

        assistant_content = ""

        for chunk in llm.stream(conversation):

            token = chunk.content

            if not token:
                continue

            assistant_content += token

            stream_queue.put(
                ("token", token)
            )

        conversation.append(
            AIMessage(content=assistant_content)
        )

        stream_queue.put(
            ("finished", None)
        )

    except Exception as e:

        stream_queue.put(
            ("error", str(e))
        )

    finally:
        waiting = False


# ==========================================================
# CHAT RENDERER
# ==========================================================

def build_chat_surface(width):

    padding = 20

    rendered_lines = []
    total_height = padding

    wrap_width = max(
        40,
        int(width / 11)
    )

    for msg in messages:

        role = msg["role"]

        role_surface = font.render(
            role.upper(),
            True,
            role_color(role)
        )

        rendered_lines.append(
            (
                role_surface,
                20,
                total_height
            )
        )

        total_height += 30

        ts_surface = tiny_font.render(
            msg["timestamp"],
            True,
            TIMESTAMP
        )

        rendered_lines.append(
            (
                ts_surface,
                20,
                total_height
            )
        )

        total_height += 22

        wrapped = textwrap.wrap(
            msg["content"],
            width=wrap_width,
            replace_whitespace=False
        )

        if not wrapped:
            wrapped = [""]

        for line in wrapped:

            txt_surface = small_font.render(
                line,
                True,
                TEXT
            )

            rendered_lines.append(
                (
                    txt_surface,
                    40,
                    total_height
                )
            )

            total_height += 24

        total_height += 18

    total_height += 20

    surface = pygame.Surface(
        (
            width,
            max(total_height, 1)
        )
    )

    surface.fill(CHAT_BG)

    for surf, x, y in rendered_lines:
        surface.blit(surf, (x, y))

    return surface, total_height


# ==========================================================
# MAIN LOOP
# ==========================================================

streaming_message = None

running = True

while running:

    WIDTH, HEIGHT = screen.get_size()

    chat_rect = pygame.Rect(
        10,
        10,
        WIDTH - 20,
        HEIGHT - 110
    )

    input_rect = pygame.Rect(
        10,
        HEIGHT - 90,
        WIDTH - 20,
        80
    )

    # ------------------------------------------------------
    # HANDLE STREAM EVENTS
    # ------------------------------------------------------

    while not stream_queue.empty():

        event, payload = stream_queue.get()

        if event == "token":

            if streaming_message is None:

                streaming_message = {
                    "role": "assistant",
                    "content": "",
                    "timestamp": timestamp()
                }

                messages.append(
                    streaming_message
                )

            streaming_message["content"] += payload

            if auto_scroll:
                scroll_offset = max_scroll

        elif event == "finished":

            streaming_message = None

            if auto_scroll:
                scroll_offset = max_scroll

        elif event == "error":

            add_message(
                "system",
                f"ERROR: {payload}"
            )

            streaming_message = None

    # ------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEWHEEL:

            scroll_offset -= event.y * 40

            auto_scroll = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_RETURN:

                if input_text.strip() and not waiting:

                    prompt = input_text.strip()

                    add_message(
                        "user",
                        prompt
                    )

                    input_text = ""

                    waiting = True

                    threading.Thread(
                        target=ask_ollama,
                        args=(prompt,),
                        daemon=True
                    ).start()

            elif event.key == pygame.K_BACKSPACE:

                input_text = input_text[:-1]

            elif event.key == pygame.K_HOME:

                scroll_offset = 0
                auto_scroll = False

            elif event.key == pygame.K_END:

                auto_scroll = True
                scroll_offset = max_scroll

            else:

                if event.unicode.isprintable():
                    input_text += event.unicode

    # ------------------------------------------------------
    # BUILD CHAT SURFACE
    # ------------------------------------------------------

    chat_surface, total_height = build_chat_surface(
        chat_rect.width
    )

    visible_height = chat_rect.height

    max_scroll = max(
        0,
        total_height - visible_height
    )

    if auto_scroll:
        scroll_offset = max_scroll

    scroll_offset = max(
        0,
        min(scroll_offset, max_scroll)
    )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    screen.fill(BG)

    pygame.draw.rect(
        screen,
        CHAT_BG,
        chat_rect,
        border_radius=8
    )

    screen.set_clip(chat_rect)

    screen.blit(
        chat_surface,
        (
            chat_rect.x,
            chat_rect.y - scroll_offset
        )
    )

    screen.set_clip(None)

    pygame.draw.rect(
        screen,
        INPUT_BG,
        input_rect,
        border_radius=8
    )

    display_text = input_text

    if waiting:

        if (pygame.time.get_ticks() // 500) % 2:
            display_text += " ▋"

    input_surface = font.render(
        display_text,
        True,
        TEXT
    )

    screen.blit(
        input_surface,
        (
            input_rect.x + 15,
            input_rect.y + 25
        )
    )

    status = (
        f"Model: {MODEL} | "
        f"Messages: {len(messages)} | "
        f"{'Generating...' if waiting else 'Ready'}"
    )

    status_surface = tiny_font.render(
        status,
        True,
        TIMESTAMP
    )

    screen.blit(
        status_surface,
        (
            15,
            HEIGHT - 105
        )
    )

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
