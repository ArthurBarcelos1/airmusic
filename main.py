import cv2
import mediapipe as mp
import numpy as np
import sounddevice as sd
import math

# =========================================
# AUDIO
# =========================================

sample_rate = 44100

current_freqs = []
phase = 0
last_sound_time = 0

# =========================================
# NOTAS
# =========================================

NOTES = [
    ("C", 261.63),
    ("C#/Db", 277.18),
    ("D", 293.66),
    ("D#/Eb", 311.13),
    ("E", 329.63),
    ("F", 349.23),
    ("F#/Gb", 369.99),
    ("G", 392.00),
    ("G#/Ab", 415.30),
    ("A", 440.00),
    ("A#/Bb", 466.16),
    ("B", 493.88),
]

NOTE_INDEX = {
    "C":0,
    "C#/Db":1,
    "D":2,
    "D#/Eb":3,
    "E":4,
    "F":5,
    "F#/Gb":6,
    "G":7,
    "G#/Ab":8,
    "A":9,
    "A#/Bb":10,
    "B":11
}

# =========================================
# HARMONIAS
# =========================================

CHORDS = {
    "maj":[0,4,7],
    "m":[0,3,7],
    "7":[0,4,7,10],
    "maj7":[0,4,7,11],
    "m7":[0,3,7,10],
    "sus2":[0,2,7],
    "sus4":[0,5,7],
    "dim":[0,3,6],
    "aug":[0,4,8],
    "m7b5":[0,3,6,10],
    "add9":[0,4,7,14]
}

selected_note = None
selected_chord = "maj"

# =========================================
# VISUAL
# =========================================

note_glow = 0
chord_glow = 0

# =========================================
# AUDIO ENGINE
# =========================================

def flute_wave(freq, t):

    return (
        1.0 * np.sin(2*np.pi*freq*t) +
        0.25 * np.sin(2*np.pi*freq*2*t) +
        0.08 * np.sin(2*np.pi*freq*3*t)
    )

# =========================================
# GERAR ACORDE
# =========================================

def generate_chord_frequencies(root_freq, chord_name):

    root_name = selected_note

    if root_name is None:
        return []

    root_index = NOTE_INDEX[root_name]

    intervals = CHORDS[chord_name]

    freqs = []

    for interval in intervals:

        semitone = (
            root_index + interval
        ) % 12

        freq = (
            root_freq *
            (2 ** (interval / 12))
        )

        freqs.append(freq)

    return freqs

# =========================================
# CALLBACK AUDIO
# =========================================

def callback(outdata, frames, time, status):

    global phase

    t = (
        np.arange(frames) + phase
    ) / sample_rate

    wave = np.zeros(frames)

    for freq in current_freqs:

        wave += flute_wave(freq, t)

    if len(current_freqs) > 0:
        wave /= len(current_freqs)

    wave *= 0.20

    phase += frames

    outdata[:] = wave.reshape(-1,1)

stream = sd.OutputStream(
    callback=callback,
    channels=1,
    samplerate=sample_rate,
    blocksize=512
)

stream.start()

# =========================================
# CAMERA
# =========================================

cap = cv2.VideoCapture(0)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)

# =========================================
# MEDIAPIPE
# =========================================

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# =========================================
# DETECTOR
# =========================================

def detect_selection(
    x,
    y,
    center,
    radius,
    items
):

    dx = x - center[0]
    dy = y - center[1]

    distance = math.sqrt(
        dx*dx + dy*dy
    )

    if distance < 90:
        return None

    if distance > radius:
        return None

    angle = (
        math.degrees(
            math.atan2(dy, dx)
        ) + 360
    ) % 360

    index = int(
        angle / (360 / len(items))
    )

    return items[index]

# =========================================
# DESENHAR RODA
# =========================================

def draw_wheel(
    frame,
    center,
    radius,
    labels,
    active,
    mode
):

    overlay = frame.copy()

    total = len(labels)

    for i, label in enumerate(labels):

        start_angle = (
            i * 360 / total
        )

        end_angle = (
            (i + 1) * 360 / total
        )

        color = (80,80,80)

        if label == active:

            if mode == "note":
                color = (80,220,255)

            else:
                color = (210,100,255)

        # FATIA

        cv2.ellipse(
            overlay,
            center,
            (radius,radius),
            0,
            start_angle,
            end_angle,
            color,
            -1
        )

        # BORDA

        cv2.ellipse(
            overlay,
            center,
            (radius,radius),
            0,
            start_angle,
            end_angle,
            (45,45,45),
            3
        )

        angle = math.radians(
            (start_angle + end_angle)/2
        )

        tx = int(
            center[0] +
            math.cos(angle) *
            (radius - 70)
        )

        ty = int(
            center[1] +
            math.sin(angle) *
            (radius - 70)
        )

        size = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2
        )[0]

        cv2.putText(
            overlay,
            label,
            (
                tx - size[0]//2,
                ty
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

    # CENTRO

    cv2.circle(
        overlay,
        center,
        90,
        (30,30,30),
        -1
    )

    # FADE

    cv2.addWeighted(
        overlay,
        0.5,
        frame,
        0.5,
        0,
        frame
    )

# =========================================
# LOOP
# =========================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame,1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb)

    # =====================================
    # POSICOES
    # =====================================

    note_center = (
        260,
        260
    )

    chord_center = (
        w - 260,
        260
    )

    radius = 220

    # =====================================
    # RODAS
    # =====================================

    draw_wheel(
        frame,
        note_center,
        radius,
        [n[0] for n in NOTES],
        selected_note,
        "note"
    )

    draw_wheel(
        frame,
        chord_center,
        radius,
        list(CHORDS.keys()),
        selected_chord,
        "chord"
    )

    # =====================================
    # TRACKING
    # =====================================

    detected_note = None
    detected_chord = selected_chord

    if results.multi_hand_landmarks:

        for hand in results.multi_hand_landmarks:

            lm = hand.landmark[8]

            x = int(lm.x * w)
            y = int(lm.y * h)

            # DEDO

            cv2.circle(
                frame,
                (x,y),
                12,
                (255,255,255),
                -1
            )

            cv2.circle(
                frame,
                (x,y),
                16,
                (180,180,180),
                2
            )

            # =================================
            # NOTA
            # =================================

            note_pick = detect_selection(
                x,
                y,
                note_center,
                radius,
                [n[0] for n in NOTES]
            )

            if note_pick:

                detected_note = note_pick

            # =================================
            # HARMONIA
            # =================================

            chord_pick = detect_selection(
                x,
                y,
                chord_center,
                radius,
                list(CHORDS.keys())
            )

            if chord_pick:

                detected_chord = chord_pick

    # =====================================
    # APLICAR
    # =====================================

    selected_note = detected_note

    if detected_chord:
        selected_chord = detected_chord

    # =====================================
    # GERAR SOM AO VIVO
    # =====================================

    current_freqs = []

    if selected_note:

        for name, freq in NOTES:

            if name == selected_note:

                current_freqs = (
                    generate_chord_frequencies(
                        freq,
                        selected_chord
                    )
                )

                last_sound_time = (
                    cv2.getTickCount()
                )

    # =====================================
    # SUSTAIN
    # =====================================

    current_time = cv2.getTickCount()

    elapsed = (
        current_time - last_sound_time
    ) / cv2.getTickFrequency()

    if elapsed > 0.15:

        current_freqs = []

    # =====================================
    # CAMERA
    # =====================================

    cv2.imshow(
        "AIR MUSIC",
        frame
    )

    key = cv2.waitKey(1)

    if key == 27:
        break

# =========================================
# FINALIZAR
# =========================================

stream.stop()

cap.release()

cv2.destroyAllWindows()