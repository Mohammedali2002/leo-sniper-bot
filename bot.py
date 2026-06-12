import os
import time
from datetime import datetime, timedelta, timezone
import requests
import telebot
from google import genai
from google.genai import types
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from threading import Thread

# -------------------------------------------------------------
# 0. خادم ويب مدمج لإبقاء السيرفر مستيقظاً 24/7 ومنعه من النوم
# -------------------------------------------------------------
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Leo Sniper Bot is Alive and Running 24/7!"

def run():
    # تشغيل السيرفر على البورت الذي يطلبه Render تلقائياً
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -------------------------------------------------------------
# 1. إعداد الرموز السرية ومفاتيح الاتصال الخاصة بك
# -------------------------------------------------------------
TELEGRAM_TOKEN = "8810768249:AAGTZvhJNL1Nkq3lRB4co7GRE0vPTtGbYc4"
GEMINI_API_KEY = "AQ.Ab8RN6Jgq3Q5ZLxzl9aJ6I4GbT_WlAaZDjyPklVcdOkhuRZ-ag"
APISPORTS_KEY = "05e424df21359af07ef98b7a2ffd5325"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# تشغيل محرك الجدولة التلقائية في الخلفية
scheduler = BackgroundScheduler()
scheduler.start()

# ذاكرة البوت المعزولة لحفظ التقرير المسبق لكل مباراة بـ ID الخاص بها لمنع الخبطة
match_database = {}

# أزرار الكيبورد الدائمة التي تظهر في أسفل شاشة الهاتف لتسهيل العمل بالملي
def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_match = telebot.types.KeyboardButton("🎯 فرز مباراة")
    btn_live = telebot.types.KeyboardButton("⏱️ فلترة حية")
    btn_cancel = telebot.types.KeyboardButton("❌ إلغاء مباراة")
    btn_purge = telebot.types.KeyboardButton("💣 تنظيف السيرفر")
    
    markup.row(btn_match, btn_live)
    markup.row(btn_cancel, btn_purge)
    return markup

# 2. البحث الذكي والمرن بكلمة واحدة عن مباريات اليوم (مباشر عبر API-Sports)
def search_todays_fixtures(keyword):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": APISPORTS_KEY
    }
    querystring = {
        "search": keyword,
        "date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(url, headers=headers, params=querystring).json()
        results =
        if "response" in response and len(response["response"]) > 0:
            for fixture in response["response"]:
                fixture_id = fixture["fixture"]["id"]
                home = fixture["teams"]["home"]["name"]
                away = fixture["teams"]["away"]["name"]
                status = fixture["fixture"]["status"]["short"]
                start_date = fixture["fixture"]["date"]
                
                # نركز فقط على المباريات التي لم تبدأ بعد أو جارية حالياً لتجهيزها
                if status in:
                    results.append({
                        "id": fixture_id,
                        "home": home,
                        "away": away,
                        "date": start_date
                    })
            return results
    except Exception as e:
        print(f"Error searching fixtures: {e}")
    return

# 3. محرك الاستطلاع المسبق بالذكاء الاصطناعي (Pre-Match Report)
def get_pre_match_report(home_team, away_team):
    prompt = f"""
    حلل هذه مباراة هذه الصورة تكتيكياً وإحصائياً بناءً على أسواقنا الأربعة (زيادة الأهداف، الركنيات، البطاقات، وفوز أحد الفريقين). 
    ركز بشكل خاص على معدل الكروت للحكم المعين وأسلوب لعب المدربين وتأثير الطقس الحار والرطوبة إن وجد.
    تجاهل الـ Odds تماماً في هذه المرحلة وأعطني التقرير الاستخباري المسبق والقسيمة الأضمن (حتى لو كانت خياراً واحداً أو لا يوجد) لنستعد للفلترة الحية.
    المباراة: {home_team} ضد {away_team}.
    """
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}]
        )
    )
    return response.text

# 4. محرك جلب الإحصائيات الحية الشاملة تلقائياً بطلب واحد ذكي (مباشر عبر API-Sports)
def fetch_live_statistics(fixture_id):
    url = "https://v3.football.api-sports.io/fixtures/statistics"
    headers = {
        "x-apisports-key": APISPORTS_KEY
    }
    querystring = {"fixture": fixture_id}
    try:
        response = requests.get(url, headers=headers, params=querystring).json()
        stats_text = ""
        if "response" in response and len(response["response"]) > 0:
            for team_data in response["response"]:
                team_name = team_data["team"]["name"]
                stats_text += f"\nإحصائيات فريق {team_name}:\n"
                for stat in team_data["statistics"]:
                    stats_text += f"- {stat['type']}: {stat['value']}\n"
            return stats_text
    except Exception as e:
        print(f"Error fetching live stats: {e}")
    return None

# 5. محرك الفلترة والقطع لإصدار قرار فوري ومختصر للغاية عند الدقيقة 15
def analyze_live_match(stats, pre_report):
    prompt = f"""
    بناءً على التقرير الاستخباري المسبق، حلل إحصائيات الدقيقة 15 لهذه المباراة.
    نريد قراراً حاسماً، فورياً ومختصراً للغاية لسرعة التنفيذ الفوري على الهاتف.
    
    قوانين صياغة الرد الإلزامية والصارمة:
    1. يجب أن يبدأ ردك مباشرة بالقرار النهائي في سطر واحد عريض باللون المناسب:
       - في حال الدخول:
         🟢 **[دخول]** - [اسم السوق باللغة العربية مع الرقم المتوقع بدقة، مثل: الركنيات أكثر من 10.5]
       - في حال الإلغاء والابتعاد:
         🔴 **[إلغاء والابتعاد فوراً]**
    2. يمنع كتابة أي مقدمات أو تحليلات طويلة.
    3. ألحق القرار بسطر ثانٍ واحد فقط لا يتجاوز 10 كلمات يوضح السبب التكتيكي الرئيسي خلف هذا القرار لزيادة الاطمئنان.
    
    التقرير المسبق:
    {pre_report}
    
    الإحصائيات الحية الكاملة عند الدقيقة 15:
    {stats}
    """
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# 6. دالة فحص حالة المباراة (تأجيل/إلغاء/تأخير) تلقائياً (مباشر عبر API-Sports)
def get_fixture_status(fixture_id):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": APISPORTS_KEY
    }
    querystring = {"id": fixture_id}
    try:
        response = requests.get(url, headers=headers, params=querystring).json()
        if "response" in response and len(response["response"]) > 0:
            return response["response"]["fixture"]["status"]["short"]
    except Exception as e:
        print(f"Error checking fixture status: {e}")
    return None

# 7. دالة الفحص والفلترة التلقائية والذكية عند الدقيقة 15
def automatic_live_filter_job(chat_id, fixture_id):
    global match_database
    if fixture_id not in match_database:
        return
        
    match_info = match_database[fixture_id]
    home = match_info["home_team"]
    away = match_info["away_team"]
    pre_report = match_info["pre_match_report"]
    
    # الفحص الاستباقي لحالة المباراة لتجنب التأجيل أو الإلغاء
    status = get_fixture_status(fixture_id)
    
    if status in:
        status_meanings = {"PST": "تأجيل", "CANC": "إلغاء", "ABD": "إيقاف/إلغاء"}
        meaning = status_meanings.get(status, "تغيير طارئ")
        bot.send_message(chat_id, f"⚠️ **تنبيه طوارئ عاجل:**\nتم رصد **{meaning}** مباراة **{home} vs {away}** رسمياً من أرض الملعب. تم إلغاء الفحص التلقائي لحماية حسابك.")
        match_database.pop(fixture_id, None)
        return
        
    if status == "NS":
        bot.send_message(chat_id, f"⏰ **تنبيه تأخير:**\nمباراة **{home} vs {away}** تأخر انطلاقها الفعلي. جاري ترحيل الفحص التلقائي بعد **15 دقيقة إضافية**.")
        new_run_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        scheduler.add_job(
            automatic_live_filter_job, 
            'date', 
            run_date=new_run_time, 
            args=[chat_id, fixture_id], 
            id=str(fixture_id)
        )
        return
        
    bot.send_message(chat_id, f"⏱️ حانت الدقيقة 15 لمباراة **{home} vs {away}**!\nجاري سحب لوحة البيانات الحية الكاملة ومطابقتها تلقائياً بالتقرير التكتيكي السابق...")
    
    live_stats = fetch_live_statistics(fixture_id)
    if not live_stats:
        bot.send_message(chat_id, f"⚠️ تعذر جلب الإحصائيات الحية لمباراة {home} vs {away} تلقائياً. يرجى مراجعتها يدوياً.")
        return
        
    decision = analyze_live_match(live_stats, pre_report)
    bot.send_message(chat_id, f"⚖️ **القرار التكتيكي النهائي التلقائي لمباراة {home} ضد {away}:**\n\n{decision}")
    
    match_database.pop(fixture_id, None)

# 8. إدارة أوامر تليجرام التفاعلية (Telegram Handlers)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = """
    ⚽ أهلاً بك يا محمد في 'منظومة القناص التلقائية المحدثة'!
    
    التحكم بالكامل من هاتفك بنقرة زر واحدة:
    1. للفرز والجدولة المسبقة:
       /match [كلمة من اسم الفريق]
       
    2. للإلغاء الفردي لمباراة مجدولة:
       /cancel
       
    3. للخيار النووي وتصفير كل الجدولة فوراً:
       /purge_all
    """
    bot.reply_to(message, welcome, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text in ["🎯 فرز مباراة", "⏱️ فلترة حية", "❌ إلغاء مباراة", "💣 تنظيف السيرفر"])
def handle_keyboard_buttons(message):
    if message.text == "🎯 فرز مباراة":
        msg = bot.reply_to(message, "🎯 اكتب الآن اسم أو جزء من اسم الفريق بالإنجليزية للبحث عنه اليوم:")
        bot.register_next_step_handler(msg, process_match_search_step)
    elif message.text == "⏱️ فلترة حية":
        handle_live_filter(message)
    elif message.text == "❌ إلغاء مباراة":
        handle_cancel_match(message)
    elif message.text == "💣 تنظيف السيرفر":
        handle_purge_all(message)

def process_match_search_step(message):
    try:
        keyword = message.text.strip()
        if not keyword:
            bot.reply_to(message, "⚠️ اسم الفريق فارغ. يرجى البدء من جديد.")
            return
            
        bot.reply_to(message, f"🔍 جاري البحث في جدول مباريات اليوم عن كلمة: **{keyword}**...")
        
        fixtures = search_todays_fixtures(keyword)
        if not fixtures:
            bot.reply_to(message, "❌ لم يتم العثور على أي مباراة جارية أو قادمة اليوم تطابق هذا الاسم.")
            return
            
        markup = telebot.types.InlineKeyboardMarkup()
        for fix in fixtures:
            button_text = f"{fix['home']} vs {fix['away']}"
            callback_data = f"prep_{fix['id']}"
            markup.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
            
        bot.reply_to(message, "🎯 اختر المباراة لتأكيد الهوية وتجهيز التقرير وجدولتها تلقائياً:", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء البحث: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('prep_'))
def process_pre_match_selection(call):
    global match_database
    try:
        fixture_id = int(call.data.replace('prep_', ''))
        chat_id = call.message.chat.id
        
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-apisports-key": APISPORTS_KEY
        }
        querystring = {"id": fixture_id}
        response = requests.get(url, headers=headers, params=querystring).json()
        
        if "response" not in response or len(response["response"]) == 0:
            bot.answer_callback_query(call.id, "❌ خطأ في جلب بيانات المباراة!")
            return
            
        fixture_data = response["response"]
        home = fixture_data["teams"]["home"]["name"]
        away = fixture_data["teams"]["away"]["name"]
        fixture_date_str = fixture_data["fixture"]["date"]
        
        bot.answer_callback_query(call.id, f"تم اختيار {home} vs {away}")
        bot.send_message(chat_id, f"⚙️ جاري تشغيل البحث وتجهيز التقرير التكتيكي المسبق لـ:\n**{home} vs {away}**...")
        
        report = get_pre_match_report(home, away)
        
        match_database[fixture_id] = {
            "home_team": home,
            "away_team": away,
            "pre_match_report": report
        }
        
        response_text = f"⚖️ **سطر تأكيد الهوية لـ 'منظومة القناص':**\n**{home} vs {away}**\n\n{report}"
        bot.send_message(chat_id, response_text, parse_mode="Markdown")
        
        start_time = datetime.fromisoformat(fixture_date_str.replace("Z", "+00:00"))
        run_time = start_time + timedelta(minutes=15)
        
        scheduler.add_job(
            automatic_live_filter_job,
            'date',
            run_date=run_time,
            args=[chat_id, fixture_id],
            id=str(fixture_id)
        )
        
        local_run_time = run_time.astimezone(timezone(timedelta(hours=3)))
        time_display = local_run_time.strftime('%I:%M:%S %p')
        
        bot.send_message(chat_id, f"⏰ **تمت الجدولة التلقائية بنجاح!**\nسأقوم بسحب الإحصائيات الكاملة وفحص ريتم الملعب تلقائياً وإرسال القرار الحاسم إلى هاتفك في تمام الساعة **{time_display}**.")
        
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ فني أثناء تأكيد الجدولة: {str(e)}")

@bot.message_handler(commands=['match'])
def handle_pre_match(message):
    try:
        keyword = message.text.replace('/match', '').strip()
        if not keyword:
            msg = bot.reply_to(message, "🎯 اكتب الآن اسم أو جزء من اسم الفريق بالإنجليزية للبحث عنه اليوم:")
            bot.register_next_step_handler(msg, process_match_search_step)
            return
            
        bot.reply_to(message, f"🔍 جاري البحث في جدول مباريات اليوم عن كلمة: **{keyword}**...")
        
        fixtures = search_todays_fixtures(keyword)
        if not fixtures:
            bot.reply_to(message, "❌ لم يتم العثور على أي مباراة جارية أو قادمة اليوم تطابق هذا الاسم.")
            return
            
        markup = telebot.types.InlineKeyboardMarkup()
        for fix in fixtures:
            button_text = f"{fix['home']} vs {fix['away']}"
            callback_data = f"prep_{fix['id']}"
            markup.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
            
        bot.reply_to(message, "🎯 اختر المباراة لتأكيد الهوية وتجهيز التقرير وجدولتها تلقائياً:", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء البحث: {str(e)}")

# 9. ميزات الإلغاء الفردي والإلغاء الشامل
def handle_cancel_match(message):
    global match_database
    if not match_database:
        bot.reply_to(message, "⚠️ لا توجد أي مباريات نشطة ومجدولة حالياً لإلغائها!")
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    for fixture_id, match_data in match_database.items():
        button_text = f"❌ إلغاء: {match_data['home_team']} vs {match_data['away_team']}"
        callback_data = f"cancel_{fixture_id}"
        markup.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
    bot.reply_to(message, "🎯 اختر المباراة التي تريد التراجع عنها وإلغاء منبهها التلقائي:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def process_cancel_selection(call):
    global match_database
    try:
        fixture_id = int(call.data.replace('cancel_', ''))
        if fixture_id not in match_database:
            bot.answer_callback_query(call.id, "⚠️ المباراة لم تعد مجدولة!")
            return
        
        match_info = match_database[fixture_id]
        
        try:
            scheduler.remove_job(str(fixture_id))
        except:
            pass
            
        match_database.pop(fixture_id, None)
        bot.answer_callback_query(call.id, "تم إلغاء المباراة بنجاح!")
        bot.send_message(call.message.chat.id, f"❌ **تم إلغاء العملية!**\nتم إيقاف منبه مباراة **{match_info['home_team']} vs {match_info['away_team']}** وحذفها من الذاكرة.")
        
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء الإلغاء: {str(e)}")

def handle_purge_all(message):
    global match_database
    if not match_database:
        bot.reply_to(message, "⚠️ الذاكرة نظيفة تماماً ولا توجد مباريات جارية لتصفيرها!")
        return
        
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="⚠️ نعم، صفّر كل شيء فوراً", callback_data="confirm_purge_all"))
    bot.reply_to(message, "❗ **تحذير نووي:** هل تريد تصفير السيرفر بالكامل وإلغاء كافة المنبهات النشطة ومسح الذاكرة؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_purge_all')
def process_purge_all(call):
    global match_database
    try:
        scheduler.remove_all_jobs()
        match_database.clear()
        
        bot.answer_callback_query(call.id, "تم تصفير السيرفر بالكامل!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ **تم مسح الذاكرة بالكامل وإيقاف كافة المؤقتات والرادارات السحابية بنجاح!**"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ فني أثناء تصفير السيرفر: {str(e)}")

def handle_live_filter(message):
    global match_database
    if not match_database:
        bot.reply_to(message, "⚠️ لا توجد مباريات مخزنة حالياً لفلترتها! ابدأ بفرز مباراة أولاً.")
        return
        
    markup = telebot.types.InlineKeyboardMarkup()
    for fixture_id, match_data in match_database.items():
        button_text = f"⏱️ فلترة: {match_data['home_team']} vs {match_data['away_team']}"
        callback_data = f"live_{fixture_id}"
        markup.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
    bot.reply_to(message, "🎯 اختر اللقاء الذي تريد فلترة إحصائياته الحية حالياً وبشكل فوري:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('live_'))
def process_live_selection(call):
    global match_database
    try:
        fixture_id = int(call.data.replace('live_', ''))
        if fixture_id not in match_database:
            bot.answer_callback_query(call.id, "⚠️ المباراة لم تعد مخزنة!")
            return
            
        match_info = match_database[fixture_id]
        bot.answer_callback_query(call.id, "جاري سحب الإحصائيات الحية...")
        bot.send_message(call.message.chat.id, f"⏱️ جاري جلب لوحة البيانات الحية الكاملة لمطابقتها لـ **{match_info['home_team']} vs {match_info['away_team']}**...")
        
        live_stats = fetch_live_statistics(fixture_id)
        if not live_stats:
            bot.send_message(call.message.chat.id, "⚠️ تعذر جلب الإحصائيات حالياً.")
            return
            
        decision = analyze_live_match(live_stats, match_info["pre_match_report"])
        bot.send_message(call.message.chat.id, f"⚖️ **القرار التكتيكي النهائي لمباراة {match_info['home_team']} ضد {match_info['away_team']}:**\n\n{decision}")
        
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء الفلترة اليدوية: {str(e)}")

# بدء تشغيل خادم الويب keep_alive لإبقاء السيرفر مستيقظاً 24/7 على Render
keep_alive()

# بدء تشغيل البوت في الخلفية باستمرار
bot.polling(none_stop=True)
