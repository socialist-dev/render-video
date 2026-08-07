const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920 });

  let html = fs.readFileSync('ui.html', 'utf8');
  const title = process.argv[2] || "Default Title";
  html = html.replace("TITLE_PLACEHOLDER", title);
  
  await page.setContent(html);

  // Tính tọa độ vùng đỏ
  const rect = await page.evaluate(() => {
    const el = document.querySelector('.container__content');
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
  });

  // Chụp ảnh PNG (trong suốt nền)
  await page.screenshot({ path: 'cover.png', omitBackground: true });
  
  // Lưu tọa độ để FFmpeg đọc
  fs.writeFileSync('coords.txt', `${rect.x}:${rect.y}:${rect.w}:${rect.h}`);
  
  console.log(`Rendered UI. Coords: ${rect.x}, ${rect.y}, ${rect.w}, ${rect.h}`);
  await browser.close();
})();
