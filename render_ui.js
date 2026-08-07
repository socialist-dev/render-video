const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: "shell",
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920 });

    const htmlPath = 'ui.html';
    if (!fs.existsSync(htmlPath)) throw new Error("File ui.html khong ton tai!");
    
    let html = fs.readFileSync(htmlPath, 'utf8');
    const title = process.argv[2] || "Tieu de mac dinh";
    html = html.replace("TITLE_PLACEHOLDER", title);
    
    await page.setContent(html, { waitUntil: 'networkidle0' });

    const rect = await page.evaluate(() => {
      const el = document.querySelector('.container__content');
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
    });

    if (!rect) throw new Error("Khong tim thay class .container__content trong HTML!");

    await page.screenshot({ path: 'cover.png', omitBackground: true });
    fs.writeFileSync('coords.txt', `${rect.x}:${rect.y}:${rect.w}:${rect.h}`);
    
    console.log(`THANH CONG: Toa do la ${rect.x}:${rect.y}:${rect.w}:${rect.h}`);
  } catch (err) {
    console.error("LOI ROI:", err.message);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
