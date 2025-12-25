import os
import logging
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from modules.fetch_content import fetch_content
from modules.export_word import export_to_word

# ✅ 設定 logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("news-export-bot")

# 載入 .env
load_dotenv()

def get_token() -> str:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("環境變數 TELEGRAM_TOKEN 未設定。請在系統或 .env 檔中設定你的 Bot Token。")
    return token

def extract_first_url(text: str) -> str | None:
    match = re.search(r"(https?://\S+)", text or "")
    return match.group(1) if match else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_text = (msg.text or "").strip()

    # ✅ 使用者輸入「匯出」
    if user_text == "匯出":
        urls = context.user_data.get("urls", [])
        if not urls:
            await msg.reply_text("目前清單是空的，請先轉傳新聞網址。", disable_web_page_preview=True)
            return

        await msg.reply_text(f"正在匯出 {len(urls)} 則新聞，請稍候…", disable_web_page_preview=True)

        try:
            output_path = await export_to_word([item["url"] for item in urls])
            await msg.reply_document(document=open(output_path, "rb"))
            context.user_data["urls"] = []
            logger.info("匯出完成，清單已清空。")
        except Exception as e:
            logger.error(f"匯出失敗：{e}")
            await msg.reply_text(f"匯出失敗：{e}", disable_web_page_preview=True)
        return

    # ✅ 使用者輸入「清空」
    if user_text == "清空":
        context.user_data["urls"] = []
        await msg.reply_text("清單已清空。", disable_web_page_preview=True)
        logger.info("使用者清空了清單。")
        return

    # ✅ 使用者輸入「清單」
    if user_text == "清單":
        urls = context.user_data.get("urls", [])
        if not urls:
            await msg.reply_text("目前清單是空的。", disable_web_page_preview=True)
        else:
            reply_text = "目前清單中的新聞：\n" + "\n".join(
                f"\n{idx+1}. {item['title']} ({item['url']})" for idx, item in enumerate(urls)
            )
            await msg.reply_text(reply_text, disable_web_page_preview=True)
        return

    # ✅ 使用者輸入「刪除 N」
    if user_text.startswith("刪除"):
        parts = user_text.split()
        if len(parts) == 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            urls = context.user_data.get("urls", [])
            if 0 <= idx < len(urls):
                removed = urls.pop(idx)
                await msg.reply_text(
                    f"已刪除第 {idx+1} 則新聞：{removed['title']} ({removed['url']})",
                    disable_web_page_preview=True
                )
                logger.info(f"刪除了第 {idx+1} 則新聞。")
            else:
                await msg.reply_text("編號不存在，請確認清單。", disable_web_page_preview=True)
        else:
            await msg.reply_text("請輸入正確格式，例如：刪除 2", disable_web_page_preview=True)
        return

    # ✅ 處理新聞網址（排除重複）
    url = extract_first_url(user_text)
    if not url:
        await msg.reply_text("請傳送新聞網址（需包含 http:// 或 https://）。", disable_web_page_preview=True)
        return

    urls = context.user_data.setdefault("urls", [])

    try:
        content = await fetch_content(url)
        title = content.split("\n", 1)[0].strip() if content else "（未能抓取標題）"
    except Exception:
        title = "（未能抓取標題）"

    if any(item["url"] == url or item["title"] == title for item in urls):
        await msg.reply_text("這則新聞已在清單中，已排除重複。", disable_web_page_preview=True)
        logger.warning("使用者嘗試加入重複新聞。")
    else:
        urls.append({"url": url, "title": title})
        await msg.reply_text(
            f"已加入清單，目前共有 {len(urls)} 則新聞。\n"
            f"輸入「匯出」整合成 Word。\n"
            f"輸入「清單」查看清單。\n"
            f"輸入「清空」清除清單。\n"
            f"輸入「刪除 N」刪除指定新聞。\n"
            f"輸入「上移 N」「下移 N」重新排序。\n"
            f"輸入「移動 N 到 M」直接移到指定位置。\n",
            disable_web_page_preview=True
        )
        logger.info(f"加入新聞：{title} ({url})")

def main(): 
    token = get_token() 
    application = Application.builder().token(token).build() 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) 
    # ✅ Webhook 模式 
    port = int(os.environ.get("PORT", 8080)) # Cloud Run 會自動提供 PORT 
    application.run_webhook( 
        listen="0.0.0.0", 
        port=port, 
        url_path=token, # 用 token 當路徑，避免隨便人呼叫 
        webhook_url=f"https://{os.environ.get('CLOUD_RUN_URL')}/{token}" 
        # 這裡要填 Cloud Run 部署後的公開網址 
    )
if __name__ == "__main__":
    main()
