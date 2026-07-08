// ── Copy file này vào: Documents/Arduino/libraries/TFT_eSPI/User_Setup.h ────
// Board: ESP32-S3 N16R8 + ST7735 1.8" 128x160

#define USER_SETUP_LOADED

#define ST7735_DRIVER
#define USE_HSPI_PORT   // Dùng SPI3 trên ESP32-S3 (tránh conflict với camera SPI2)
#define TFT_WIDTH  128
#define TFT_HEIGHT 160

#define TFT_MOSI 41   // SDA
#define TFT_SCLK 42   // CLK
#define TFT_CS    2   // CS
#define TFT_DC    1   // RS/DC
#define TFT_RST  21   // RST

// Tab màu — thử GREENTAB hoặc REDTAB nếu màu sai
#define ST7735_BLACKTAB

#define LOAD_GLCD
#define LOAD_FONT2
#define LOAD_FONT4

#define SPI_FREQUENCY  27000000
