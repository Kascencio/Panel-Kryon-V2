#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

/* ===== Config básica (2 salidas) =====
   strip[0] -> GPIO 5  (SP901E/DAT2 -> tiras 1,3,4)
   strip[1] -> GPIO 18 (SP901E/DAT4 -> tiras 2,5,6,7)
*/
#define N_STRIPS 2
#define N_LEDS   170
const uint8_t PINS[N_STRIPS] = {2, 4};

/* ===== Self-test / Auto-start ===== */
#define SELFTEST_TOTAL_MS   20000     // 20 s totales (R,G,B ~6.6 s cada uno)
#define SELFTEST_BRIGHT     20        // brillo durante el self-test (%)
#define SELFTEST_AUTOSTART  false     // true => al terminar arranca AUTO_START_MODE
#define AUTO_START_MODE     CASC      // modo a arrancar si SELFTEST_AUTOSTART = true

/* ===== NeoPixel ===== */
Adafruit_NeoPixel strip[N_STRIPS] = {
  Adafruit_NeoPixel(N_LEDS, PINS[0], NEO_GRB + NEO_KHZ800),
  Adafruit_NeoPixel(N_LEDS, PINS[1], NEO_GRB + NEO_KHZ800)
};

/* ===== Intensidad global ===== */
uint8_t intensidad = 50;  // 0–100 %
void applyBrightness() {
  uint8_t b = map(intensidad, 0, 100, 0, 255);
  for (uint8_t i = 0; i < N_STRIPS; i++) strip[i].setBrightness(b);
  for (uint8_t i = 0; i < N_STRIPS; i++) strip[i].show();
}

/* ===== Colores ===== */
uint32_t ROJO()   { return strip[0].Color(255, 0,   0); }
uint32_t VERDE()  { return strip[0].Color(0,   255, 0); }
uint32_t AZUL()   { return strip[0].Color(0,   0, 255); }
uint32_t colFrom(uint8_t idx){ return (idx==0)?ROJO():(idx==1)?VERDE():AZUL(); }
inline uint8_t nextCol(uint8_t c){ return (c+1)%3; }
const uint32_t OFF = 0;

/* ===== Utilidades ===== */
#define LEN(x) (uint8_t)(sizeof(x)/sizeof(x[0]))
void fillStrip(uint8_t s, uint32_t c){
  for(uint16_t i=0;i<N_LEDS;i++) strip[s].setPixelColor(i,c);
}
void fillAll(uint32_t c){
  for(uint8_t s=0;s<N_STRIPS;s++) fillStrip(s,c);
  for(uint8_t s=0;s<N_STRIPS;s++) strip[s].show();
}
void clearAll(){ fillAll(OFF); }

/* ===== Grupos por salida ===== */
const uint8_t GA[] = {0};   // Grupo A: GPIO5
const uint8_t GB[] = {1};   // Grupo B: GPIO18

/* ===== GENERAL por pasos (igual que tu patrón) ===== */
struct Paso {
  uint32_t colA;  uint32_t colB;
  bool     blinkA; bool   blinkB;
  uint32_t dur;   // ms
};
static const Paso pasos[] = {
  {AZUL(),  ROJO(),  true , false, 30000},
  {ROJO(),  AZUL(),  false, true , 20000},
  {VERDE(), VERDE(), true , false, 30000},
  {AZUL(),  ROJO(),  false, true , 20000},
  {AZUL(),  ROJO(),  true , false, 10000},
  {ROJO(),  AZUL(),  true , false, 30000},
  {ROJO(),  VERDE(), true , false, 30000},
  {VERDE(), VERDE(), false, true , 20000},
  {AZUL(),  AZUL(),  false, true , 30000}
};
static const uint8_t N_PASOS = sizeof(pasos)/sizeof(pasos[0]);

/* ===== Estado global ===== */
enum Modo { OFFLINE, GENERAL, MONO_R, MONO_V, MONO_A, MONO_W, INTERM, PAUSA, CASC, CASC_REV };
Modo modo = OFFLINE;
bool activo = false;

/* ===== Timers / estados animaciones ===== */
uint8_t   idxPaso  = 0;
uint32_t  tPaso    = 0;
uint32_t  tBlink   = 0;
bool      blinkOn  = true;
const uint32_t BLINK_MS = 100;

uint32_t tSwap = 0; uint8_t idxColor = 0;
uint32_t tCas  = 0; const uint32_t CAS_DELAY = 50;
uint16_t posCasc = 0; uint8_t colCasc = 0;

/* ===== cascREV (dual por grupos) ===== */
#define INVERT_A       true   // Grupo A (GPIO5) abajo->arriba
#define INVERT_B       false  // Grupo B (GPIO18) normal
#define CLEAR_ON_CYCLE false  // true: limpiar al cambiar de color

/* ===== Self-test no bloqueante (10 s totales) ===== */
bool     selftestActive  = false;
uint8_t  selftestIndex   = 255;        // 255 = sin color aplicado aún
uint32_t selftestStartAt = 0;
uint32_t selftestPerCol  = 0;
uint8_t  savedIntensity  = 50;

void startSelfTest(){
  if (SELFTEST_TOTAL_MS == 0) { selftestActive = false; return; }
  savedIntensity = intensidad;
  intensidad = SELFTEST_BRIGHT;
  applyBrightness();

  selftestPerCol  = SELFTEST_TOTAL_MS / 3;   // ~3333 ms por color
  selftestStartAt = millis();
  selftestIndex   = 255;                     // fuerza pintar el primer color en el primer tick
  selftestActive  = true;
}

void endSelfTest(bool autostart){
  clearAll();                     // ← apaga
  intensidad = savedIntensity;
  applyBrightness();
  selftestActive = false;

  if (autostart){
    modo = AUTO_START_MODE;       // arranca el modo elegido
    activo = true;
    idxPaso=0; tPaso=tBlink=millis(); blinkOn=true;
    idxColor=0; tSwap=tPaso; posCasc=0; colCasc=0; tCas=tPaso;
    Serial.println(">> AutoStart tras self-test @" + String(intensidad) + "%");
  } else {
    activo = false;               // queda apagado
    modo = OFFLINE;
    Serial.println(">> Self-test finalizado. LEDs apagados.");
  }
}

void runSelfTestTick(){
  if (!selftestActive) return;

  uint32_t now = millis();
  uint32_t elapsed = now - selftestStartAt;

  // Corte de seguridad por tiempo total
  if (elapsed >= SELFTEST_TOTAL_MS){
    endSelfTest(SELFTEST_AUTOSTART);
    return;
  }

  // Determina qué color toca por tiempo transcurrido
  uint8_t slot = elapsed / selftestPerCol;   // 0,1,2
  if (slot > 2) slot = 2;

  if (slot != selftestIndex){
    selftestIndex = slot;
    fillAll(colFrom(selftestIndex));         // pinta R/G/B según el slot
  }
}

/* ===== Patrones ===== */
void runGeneralBySteps() {
  uint32_t ahora = millis();
  const Paso& p = pasos[idxPaso];

  if ((p.blinkA || p.blinkB) && (ahora - tBlink >= BLINK_MS)) {
    blinkOn = !blinkOn;
    tBlink  = ahora;
  }
  for (uint8_t i = 0; i < LEN(GA); i++) {
    uint8_t s = GA[i];
    fillStrip(s, p.blinkA ? (blinkOn ? p.colA : OFF) : p.colA);
  }
  for (uint8_t i = 0; i < LEN(GB); i++) {
    uint8_t s = GB[i];
    fillStrip(s, p.blinkB ? (blinkOn ? p.colB : OFF) : p.colB);
  }
  for (uint8_t s = 0; s < N_STRIPS; s++) strip[s].show();

  if (ahora - tPaso >= p.dur) {
    idxPaso = (idxPaso + 1) % N_PASOS;
    tPaso   = ahora;
    blinkOn = true;
    tBlink  = ahora;
  }
}

/* MONO fijo (sin parpadeo) */
uint32_t lastMonoColor = 0;
bool monoActive = false;
void runMonoSolid(uint32_t color){
  if (!monoActive || lastMonoColor != color){
    fillAll(color);
    lastMonoColor = color;
    monoActive = true;
  }
}

/* Intermitente / Pausado (todas las tiras cambian R->G->B) */
void runInterm(uint32_t intv){
  uint32_t now = millis();
  if(now - tSwap >= intv){
    idxColor = (idxColor + 1) % 3;
    uint32_t c = colFrom(idxColor);
    fillAll(c);
    tSwap = now;   // captura única para evitar deriva de tiempo
  }
}

/* ===== CASC (extraída tal cual) ===== */
void runCascExtracted(){
  uint32_t now = millis();
  if(now - tCas >= CAS_DELAY){
    if(posCasc < N_LEDS){
      uint32_t c = colFrom(colCasc);
      for(uint8_t s=0;s<N_STRIPS;s++){
        strip[s].setPixelColor(posCasc, c);
        strip[s].show();
      }
      posCasc++;
    } else {
      posCasc = 0;
      colCasc = nextCol(colCasc);
    }
    tCas = now;
  }
}

/* ===== cascREV (dual por grupos: A invertido, B normal) ===== */
void runCascRevDual(){
  uint32_t now = millis();
  if(now - tCas >= CAS_DELAY){
    uint32_t c = colFrom(colCasc);
    uint16_t pos  = posCasc;
    uint16_t idxA = INVERT_A ? (N_LEDS-1 - pos) : pos;
    uint16_t idxB = INVERT_B ? (N_LEDS-1 - pos) : pos;

    for (uint8_t i = 0; i < LEN(GA); i++) strip[GA[i]].setPixelColor(idxA, c);
    for (uint8_t i = 0; i < LEN(GB); i++) strip[GB[i]].setPixelColor(idxB, c);
    for (uint8_t s = 0; s < N_STRIPS; s++) strip[s].show();

    posCasc++;
    if (posCasc >= N_LEDS){
      posCasc = 0;
      colCasc = nextCol(colCasc);
      if (CLEAR_ON_CYCLE) clearAll();
    }
    tCas = now;
  }
}

/* ===== Comandos Serial/WebSerial =====
   - inicio:cascada,50    -> CASC
   - inicio:cascrev,50    -> cascREV
   - inicio:rojo,60       -> MONO_R a 60%
   - test                 -> inicia self-test de 10 s (no bloqueante)
   - test:off             -> cancela/termina el self-test de inmediato (queda apagado)
   - stop                 -> detiene animaciones y también cancela self-test
*/
void processCmd(const String& cmd){
  String c = cmd; c.trim();

  if(c.startsWith("inicio:")){
    int p = c.indexOf(','), q = c.indexOf(':');
    String m = (p>-1)? c.substring(q+1,p) : c.substring(q+1);
    String ml = m; ml.toLowerCase();

    // si hay self-test, cancelarlo antes de cambiar modo
    if (selftestActive) endSelfTest(false);

    if(p>-1) { intensidad = constrain(c.substring(p+1).toInt(), 0, 100); applyBrightness(); }

    if      (ml=="general")      { modo = GENERAL; }
    else if (ml=="rojo")         { modo = MONO_R; monoActive=false; }
    else if (ml=="verde")        { modo = MONO_V; monoActive=false; }
    else if (ml=="azul")         { modo = MONO_A; monoActive=false; }
    else if (ml=="blanco")       { modo = MONO_W; monoActive=false; }
    else if (ml=="intermitente") { modo = INTERM; }
    else if (ml=="pausado")      { modo = PAUSA; }
    else if (ml=="cascada" || ml=="casc") { modo = CASC; }
    else if (ml=="cascrev") { modo = CASC_REV; }

    activo = true;
    idxPaso=0; tPaso=tBlink=millis(); blinkOn=true;
    idxColor=0; tSwap=tPaso; posCasc=0; colCasc=0; tCas=tPaso;

    Serial.println(">> Iniciado: " + m + " @" + String(intensidad) + "%");
  }
  else if(c.startsWith("intensidad:")){
    intensidad = constrain(c.substring(c.indexOf(':')+1).toInt(), 0, 100);
    applyBrightness();
    Serial.println(">> Intensidad: " + String(intensidad) + "%");
  }
  else if(c=="test"){
    startSelfTest();
    Serial.println(">> Self-test iniciado (10 s totales)");
  }
  else if(c=="test:off" || c=="skiptest"){
    if (selftestActive){
      endSelfTest(false);  // queda apagado
      Serial.println(">> Self-test cancelado");
    }
  }
  else if(c=="stop" || c=="completado"){
    // Cancelar self-test primero para restaurar intensidad guardada
    if (selftestActive){ endSelfTest(false); }
    activo = false; modo = OFFLINE; clearAll(); monoActive=false;
    Serial.println(">> Detenido");
  }
}

/* ===== Setup / Loop ===== */
void setup(){
  Serial.begin(115200);
  for(uint8_t i=0;i<N_STRIPS;i++){ strip[i].begin(); strip[i].show(); }
  applyBrightness();

  // LEDs apagados al arrancar (self-test disponible con comando 'test')
  clearAll();
  Serial.println(">> Sistema listo. LEDs apagados.");
}

void loop(){
  // 1) Tick del self-test (si está activo)
  runSelfTestTick();

  // 2) Animaciones normales (solo si NO hay self-test activo)
  if(!selftestActive && activo){
    switch(modo){
      case GENERAL:   runGeneralBySteps();            break;
      case MONO_R:    runMonoSolid(ROJO());           break;
      case MONO_V:    runMonoSolid(VERDE());          break;
      case MONO_A:    runMonoSolid(AZUL());           break;
      case MONO_W:    runMonoSolid(strip[0].Color(255,255,255)); break;
      case INTERM:    runInterm(200);                 break;
      case PAUSA:     runInterm(1500);                break;
      case CASC:      runCascExtracted();             break;
      case CASC_REV:  runCascRevDual();               break;
      default:                                          break;
    }
  }

  // 3) Comandos
  if(Serial.available()){
    processCmd(Serial.readStringUntil('\n'));
  }
}