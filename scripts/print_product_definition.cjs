/** 使用本地浏览器打印产品定义；限制网络并检查图片完整加载。 */
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
async function main() {
  const [input, output, modulePath] = process.argv.slice(2);
  if (!input || !output || !modulePath) throw Error('用法：脚本 HTML PDF Playwright路径');
  if (fs.existsSync(output)) throw Error('拒绝覆盖已有PDF');
  const {chromium} = require(modulePath);
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1000,height:1400}});
    await page.route('**/*', r => ['file:','data:','about:'].includes(new URL(r.request().url()).protocol) ? r.continue() : r.abort());
    await page.goto(pathToFileURL(path.resolve(input)).href);
    await page.evaluate(() => document.fonts.ready);
    const result = await page.evaluate(() => ({
      headings:[...document.querySelectorAll('h2')].map(e=>e.textContent),
      images:[...document.images].map(i=>({loaded:i.complete && i.naturalWidth>0, alt:i.alt}))
    }));
    if(result.headings.length!==7 || result.images.length!==3 || result.images.some(i=>!i.loaded)) throw Error(JSON.stringify(result));
    await page.pdf({path:output,preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,
      headerTemplate:'<span></span>',
      footerTemplate:'<div style="width:100%;text-align:center;font-size:9px;color:#65788f">Auto Git · 0.2 审阅稿　<span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1});
