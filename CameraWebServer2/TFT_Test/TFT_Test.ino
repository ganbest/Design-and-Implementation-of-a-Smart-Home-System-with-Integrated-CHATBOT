#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>

// Sửa đúng theo chân bạn đang cắm
#define TFT_CLK   42   // CLK / SCK
#define TFT_SDA   41   // SDA / MOSI
#define TFT_CS    2    // CS
#define TFT_RS    1    // RS = DC
#define TFT_RST   21   // RST

// Software SPI: CS, DC, MOSI, SCLK, RST
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_RS, TFT_SDA, TFT_CLK, TFT_RST);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Start TFT test");

  // Thử BLACKTAB trước
  tft.initR(INITR_BLACKTAB);

  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);

  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(2);
  tft.setCursor(10, 20);
  tft.println("SMART");

  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 50);
  tft.println("DOOR");

  tft.fillRect(10, 85, 60, 30, ST77XX_RED);
  tft.fillCircle(110, 100, 15, ST77XX_BLUE);

  Serial.println("Done");
}

void loop() {
}