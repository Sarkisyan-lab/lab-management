#!/usr/bin/env python
# coding: utf-8

# # Imports

import logging


console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


import sys
import os
import re
import subprocess
import tempfile
import datetime
import pathlib
from time import sleep
from os import listdir, mkdir, getenv
from os.path import isfile, join, exists
import signal
import threading
import random


from telegram import parsemode 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *


from pyairtable.formulas import match





# # Constants

# telegram bot token
TOKEN = os.environ['SYNBIO_TELEGRAM_BOT_TOKEN']


working_dir = pathlib.Path(tempfile.gettempdir())


# Instanciate tables,
# list fields to display when user requests a record
# using the metadata API

schema = get_base_schema(Base(api_key,base_id))

table_IDs=dict()
fields_to_keep=dict()
tables=dict()
table_schemas=dict()

for table_schema in schema['tables']:
    
    table_name=table_schema.get("name")
    table_id=table_schema.get("id")
    fields = table_schema.get("fields")
    
    for field in fields:
        if "[chatbot]" in field.get("description",str()):
            table_schemas[table_name]=table_schema
            fields_to_keep.setdefault(table_name,list())
            fields_to_keep[table_name].append(field.get("name"))
            table_IDs[table_name]=table_id
            tables[table_name]=get_table(table_id)


quotes=[
    "Nothing inspires cleanliness more than an unexpected H&S audit.",
    "Our lab is clean enough to be healthy, and dirty enough to be happy.",
    "Everybody wants to save the earth but no one wants to help me empty the yellow bins!",
    "We dream of having a clean lab — but who dreams of actually doing the cleaning?",
    "Have you ever taken a labcoat out of the clothes basket because it had become, relatively, the cleaner thing?",
    "Cleaning the lab can't kill you, but why take the chance? ;)",
    "Dust is not a protective coating for fine benches.",
    "My theory on cleaning the lab is: label it! Then, if the item doesn't multiply, smell, catch fire, or block the refrigerator door, let it be.",
    "I find cleaning the lab cathartic.",
    "My daughter wanted a Cinderella themed party so I invited all her friends over and made them clean the lab.",
    "Your idea of cleaning the lab should probably be more than to sweep the room with a glance.",
    "Just cleaned my whole lab from top to bottom, so now I’m going to need everybody to stop working here.",
    "You never know what you have, until you clean your lab.",
    "I get more cleaning done in the 10 minutes before the H&S audit than I do in a week.",
    "I was going to clean the lab, but then somebody commented on my data.",
    "A spotless lab is a sign of a misspent life.",
    "Labkeeping ain’t no joke.",
    "A relaxed mind is a creative mind.",
    "Act, don’t react.",
    "Be so happy that when others look at you they become happy too.",
    "Compassion has no limit. Kindness has no enemy",
    "Every smile is a direct achievement.",
    "Empty yourself and let the universe fill you.",
    "Gratitude is the open door to abundance.",

    "Have wisdom in your actions and faith in your merits.",
    "Happiness comes when you overcome the most impossible challenge.",
    "It’s not life that matters; it’s the courage that we bring to it.",
    "Inspiration is an unlimited power.",
    "Listen and you will develop intuition.",
    "Love what is ahead by loving what has come before.",
    "Love is unchanging and limitless.",
    "Life is a chance. Love is infinity. Grace is reality.",
    "Provoke, confront, elevate.",
    "Real happiness lies in that which never comes nor goes but simply is.",
    "The beauty in you is your spirit. The strength in you is your endurance. The intelligence in you is your vastness.",
    "There is no love without compassion.",
    "The beauty in you is your spirit.",
    "To know others is smart. To know yourself is wise.",
    "Whatever you are, you are. Be proud of it.",
    "Work but don’t forget to live.",
    "Your word is your greatest power.",
    "Your life is based on the capacity of energy in you not outside of you. TC mark",
    "Act selfless, you will be infinite.",
    "Appreciate yourself and honor your soul.",
    "As a plant can’t live without roots, so a human can’t live without a soul.",
    "A relaxed mind is a creative mind.",
    "An attitude of gratitude brings you many opportunities.",
    "Act, don’t react.",
    "Always be pure, simple and honest.",
    "All knowledge is within you.",
    "Be proud of who you are.",
    "By honoring your words, you are honored.",
    "Bliss cannot be disturbed by gain or loss.",
    "By honoring your words, you are honored in this world.",
    "Be Happy so long as breath is in you.",
    "Be so happy that when others look at you they become happy too.",
    "Bliss is a constant state of mind, undisturbed by gain or loss.",
    "Be great, feel great and act great.",
    "By listening, you comfort another person.",
    "By kind and compassionate and the whole world will be your friend.",
    "Better to slip with your feet than with your tongue.",
    "Compassion has no limit. Kindness has no enemy.",
    "Chance multiply if you grab them.",
    "Delight the world with kindness, grace and compassion.",
    "Don’t sleep counting sheep, Count blessings, then sleep",
    "Dignity and tranquility last forever.",
    "Don’t take pride in taking. Give and you will be given virtues.",
    "Delight the world with your compassion, kindness and grace.",
    "Don’t let yourself down, anyone else down or participate in a let down",
    "Develop your intuition.",
    "Every heartbeat creates a miracle.",
    "Every smile is a direct achievement.",
    "Experience is wisdom.",
    "Experience the warmth and love of your soul.",
    "Empty yourself and let the universe fill you.",
    "Experience your own body, your own mind and your own soul.",
    "Every promise is a present in abundance.",
    "Every promise is a present in advancement.",
    "Feel great, act great and be great.",
    "Feel great, act great and approve of yourself.",
    "Feel God within you with each breath.",
    "Find happiness within yourself. Then share yourself with others.",
    "For every loss there’s an equal gain, for every gain there’s an equal loss.",
    "Feel good, be good and do good.",
    "Grace brings contentment.",
    "Grace brings trust, appreciation, love and prosperity.",
    "Gratitude is the open door to abundance.",
    "Greatness is measured by your gifts, not your possessions.",
    "Goodness should become human nature, because it real in nature.",
    "Happiness comes from contentment.",
    "Happiness is every human being’s birthright.",
    "Have wisdom in your actions and faith in your merits.",
    "Happiness is nothing but total relaxation.",
    "Happiness comes when you overcome the most impossible challenge.",
    "Happiness is nothing but total relaxation.",
    "It’s not life that matters; it’s the courage that we bring to it.",
    "Inspiring others towards happiness brings you happiness.",
    "I am beautiful, I am bountiful, I am blissful.",
    "It is not what you have that is your greatness; it is what you can give.",
    "It’s important to find your identity and your legacy.",
    "In order to be remembered, leave nothing behind but goodness.",
    "If you don’t love where you come from, you can’t love where you are going.",
    "If you see good, learn something. If you see bad, learn what not to be.",
    "Inspiration is an unlimited power.",
    "Joy is the essence of success.",
    "Know whatever you are doing is the most beautiful thing.",
    "Keep up.",
    "Listen and you will develop intuition.",
    "Let Your Manners Speak for You.",
    "Let things come to you.",
    "Love, compassion and kindness are the anchors of life.",
    "Let your heart speak to others’ hearts.",
    "Love is where compassion prevails and kindness rules.",
    "Live from your heart and you will be most effective.",
    "Let your heart guide you.",
    "Love what is ahead by loving what has come before.",
    "Live in your strength.",
    "Live for each other.",
    "Love your soul.",
    "Live to share.",
    "Love is unchanging and limitless.",
    "Live with reverence for yourself and others.",
    "Life is a flow of love; your participation is requested.",
    "Life is a chance. Love is infinity. Grace is reality.",
    "Love has no fear and no vengeance.",
    "Love is ecstasy.",
    "Let Love elevate your self to excellence.",
    "Let People bask in your radiance and sunshine.",
    "Life is a gift. If you do not value your gift, nobody else will.",
    "Learn to be noble, courteous and committed.",
    "Live by intuition and consciousness",
    "Live and let live.",
    "Let your mind dance with your body.",
    "Love is to live for each other.",
    "Man is as vast as he acts.",
    "May you inner self be secure and happy.",
    "Make yourself so happy that when others look at you they become happy too.",
    "Meditation is the medicine of the mind.",
    "Mental happiness is total relaxation.",
    "May this day bring you peace, tranquility and harmony.",
    "May your light become a living universal light.",
    "May you have faith in your worth and act with wisdom.",
    "May you have love, kindness and compassion for all living things.",
    "May your mind learn to love with compassion.",
    "Nature is a true giver, a true friend and a sustainer.",
    "Noble language and behaviors are so powerful that hearts can be melted.",
    "Our intuition lies in our innocence.",
    "Old age needs wisdom and grace.",
    "Open up to infinity and you become infinity.",
    "Oneness is achieved by recognizing your self.",
    "One of the best actions we can take with courage is to relax.",
    "Obey, serve, love and excel.",
    "Our thoughts are forming the world.",
    "Practice kindness, mercy and forgiveness.",
    "Practice kindness, compassion and caring.",
    "Provoke, confront, elevate.",
    "Patience gives the power to practice; practice gives the power that leads to perfection.",
    "Radiate the infinite light through your finite self.",
    "Recognize that you are the truth.",
    "Recognize that the other person is you.",
    "Real happiness lies in that which never comes nor goes but simply is.",
    "Say it straight, simple and with a smile.",
    "Soul is the highest self.",
    "Socialize with compassion and kindness.",
    "Speak the truth.",
    "Sing from your heart.",
    "Share your strengths, not your weaknesses.",
    "Self-reliance conquers any difficulty.",
    "Serve humanity so that people feel we are kind to them.",
    "Serve all without classification or discrimination",
    "Socialize with compassion, kindness and grace.",
    "Strength does not lie in what you have. It lies in what you can give.",
    "The moment you love, you are unlimited.",
    "The beauty in you is your spirit. The strength in you is your endurance. The intelligence",
    "in you is your vastness.",
    "The power of love is infinite.",
    "The universe is the stage on which you dance, guided by your heart.",
    "The art of happiness is to serve all.",
    "To be great, feel great and act great.",
    "The purpose of life is to enjoy every moment.",
    "To learn, read. To know, write. To master, teach.",
    "Truth is everlasting.",
    "To be calm is the highest achievement of the self.",
    "The beauty in you is your spirit.",
    "There is no greater power than the power of the word.",
    "The soul is projection: represent it.",
    "There is no greater power in this universe than the power of prayer.",
    "The mind is energy: regulate it.",
    "The Power of love is infinite.",
    "There is no love without compassion.",
    "There is nothing more precious than the self.",
    "The only tool you need is kindness.",
    "The body is a temple: take care of it.",
    "True understanding is found through compassion.",
    "Those who are selfless find God.",
    "The beauty of life is to experience yourself.",
    "The power of prayer extends happiness.",
    "There is beauty in your presence. Show who you are.",
    "Travel light, live light, spread the light, be the light.",
    "There are three values: Feel good, be good and do good.",
    "True wealth is the ability to let go of your possessions.",
    "To be healthy: eat right, walk right and talk to yourself right.",
    "True understanding is found through compassion.",
    "Those who live in the past limit their future.",
    "The trust that others place in you is your grace.",
    "The best way of life is to be, simply be.",
    "The greatest tool you have is to listen.",
    "The rhythm of life is when you experience your own body, mind and soul.",
    "The beauty in you is your spirit.",
    "The universe is a stage on which your mind dances with your body, guided by your heart.",
    "Tranquility is the essence of life",
    "The art of longing and the art of belonging must be experienced in life.",
    "To know others is smart. To know yourself is wise.",
    "Trust creates peace.",
    "Trust the wisdom of the heart.",
    "The heart sees deeper than the eye.",
    "Uplift everybody and uplift yourself.",
    "Understanding is found through compassion.",
    "Unite with your own higher self and create a friendship.",
    "When ego is lost, limit is lost.",
    "When you know that all is light, you are enlightened.",
    "Where there is love, there is no question.",
    "When we practice listening, we become intuitive.",
    "Wisdom, character and consciousness conquer everything.",
    "Wisdom becomes knowledge when it is a personal experience.",
    "Whatever you are doing is the most beautiful thing.",
    "Without realizing who you are, happiness cannot come to you.",
    "We are spiritual beings having a human experience.",
    "When the mind is backed by will, miracles happen.",
    "Whatever character you give your children shall be their future.",
    "Whatever you are, you are. Be proud of it.",
    "When the ego is lost, limit is lost. You become infinite, kind, beautiful.",
    "We are here to love each other, serve each other and uplift each other.",
    "When the mind is backed by will, miracles happen.",
    "When you are in tune with the unknown, the known is peaceful.",
    "Work but don’t forget to live.",
    "You are unlimited.",
    "You are a living consciousness.",
    "Your mind is the flow of God.",
    "You head must bow to your heart.",
    "Your intuition is your best friend.",
    "You are remembered for your goodness.",
    "Your word is your greatest power.",
    "Your destiny is to merge with infinity.",
    "Your heartbeat is the rhythm of your soul.",
    "Your greatest strength is love.",
    "Your infinity in you is the reality in you.",
    "Your breath is the voice of your soul.",
    "Your greatness is measured by your gifts, not by what you have.",
    "You must know that you can swim through every tide and change of time.",
    "You only give when you love.",
    "Your life is based on the capacity of energy in you not outside of you.",
    "You are infinite.",
    "You can run after satisfaction, but satisfaction must come from within.",
    "Your greatness is not what you have; it’s what you give.",
    "You will feel fulfilled when you do the impossible for someone else.",
    "Your soul is your highest self.",
    "Your strength is in how calmly, quietly and peacefully you face life.",
    "You must live for something higher, bigger and better than you.",
    "Success is not the key to happiness. Happiness is the key to success. If you love what you are doing, you will be successful.\nAlbert Schweitzer",
    "Don't watch the clock; do what it does. Keep going.\nSam Levenson",
    "Choose a job you love, and you will never have to work a day in your life.\nConfucius",
    "The future depends on what you do today.\nMahatma Gandhi",
    "The only limit to our realization of tomorrow will be our doubts of today.\nFranklin D. Roosevelt",
    "Hard work beats talent when talent doesn't work hard.\nTim Notke",
    "I’m a greater believer in luck, and I find the harder I work the more I have of it.\nThomas Jefferson",
    "Start where you are. Use what you have. Do what you can.\nArthur Ashe",
    "Success doesn't come from what you do occasionally. It comes from what you do consistently.\nMarie Forleo",
    "The difference between ordinary and extraordinary is that little extra.\nJimmy Johnson",
    "Believe you can and you're halfway there.\nTheodore Roosevelt",
    "The only way to achieve the impossible is to believe it is possible.\nCharles Kingsleigh",
    "It always seems impossible until it's done.\nNelson Mandela",
    "The best way to predict the future is to create it.\nAbraham Lincoln",
    "Do not wait to strike till the iron is hot; but make it hot by striking.\nWilliam Butler Yeats",
    "Opportunities don't happen. You create them.\nChris Grosser",
    "Whether you think you can, or you think you can't\nyou're right.\nHenry Ford",
    "Great things are done by a series of small things brought together.\nVincent Van Gogh"]

funny_words=["abecedarian","abracadabra","accoutrements","adagio","aficionado","agita","agog","akimbo","alfresco","aloof","ambrosial","amok","ampersand","anemone","anthropomorphic","antimacassar","aplomb","apogee","apoplectic","appaloosa","apparatus","archipelago","atingle","avuncular","azure","babushka","bailiwick","bafflegab","balderdash","ballistic","bamboozle","bandwagon","barnstorming","beanpole","bedlam","befuddled","bellwether","berserk","bibliopole","bigmouth","bippy","blabbermouth","blatherskite","blindside","blob","blockhead","blowback","blowhard","blubbering","bluestockings","boing","boffo (boffola)","bombastic","bonanza","bonkers","boondocks","boondoggle","borborygmus","bozo","braggadocio","brainstorm","brannigan","breakneck","brouhaha","buckaroo","bucolic","buffoon","bugaboo","bugbear","bulbous","bumbledom","bumfuzzle","bumptious","bumpkin","bungalow","bunkum","bupkis","burnsides","busybody","cacophony","cahoots","calamity","calliope","candelabra","canoodle","cantankerous","catamaran","catastrophe","catawampus","caterwaul","chatterbox","chichi","chimerical","chimichanga","chitchat","clandestine","claptrap","clishmaclaver","clodhopper","cockamamie","cockatoo","codswallop","collywobbles","colossus","comeuppance","concoction","conniption","contraband","conundrum","convivial","copacetic","corkscrew","cornucopia","cowabunga","coxcomb","crackerjack","crescendo","crestfallen","cryptozoology","cuckoo","curlicue","curmudgeon","demitasse","denouement","derecho","desperado","diaphanous","diddly-squat","digeridoo","dilemma","dillydally","dimwit","diphthong","dirigible","discombobulated","dodecahedron","doldrums","donkeyman","donnybrook","doodad","doohickey (this is what I call a library due date card)","doppelganger","dumbfounded","dumbwaiter","dunderhead","earwig","eavesdrop","ebullient","effervescence","egads","eggcorn","egghead","elixir","ephemeral","epiphany","ersatz","eucatastrophe","extraterrestrial","finagle","fandango","festooned","fez","fiasco","fiddle-footed","fiddlesticks","finicky","firebrand","fishwife","fisticuffs","flabbergasted","flapdoodle","flibbertigibbet","flimflam","flippant","floccinaucinihilipilification","flophouse","flotsam","flummery","flummoxed","flyaway","flyspeck","folderol","foofaraw","foolhardy","foolscap","footloose","fopdoodle","fortuitous","fracas","frangipani","freewheeling","fricassee","frippery","frogman","froufrou","fuddy-duddy","fussbudget","futz","gadfly","gadzooks","gallimaufry","gambit","gangplank","gangway","gargoyle","gasbag","gazebo","gazpacho","gewgaw","genteel","ghostwriter","gibberish","gimcrack","gizmo","glabella","glitch","globetrotter","gobbledygook","gobsmacked","goosebump","gooseflesh","gorgonzola","gossamer","grandiloquent","greenhorn","guffaw","gumshoe","guru","gussied","guttersnipe","haberdashery","haboob","hairpin","halcyon","halfwit","hangdog","haphazard","harebrained","harumph","harum-scarum","headlong","heartstrings","heebie-jeebie","heirloom","helter-skelter","hemidemisemiquaver","heyday","higgledy-piggledy","highfalutin","hijinks","hillbilly","hippocampus","hippogriff","hobbledehoy","hobnobbed","hocus-pocus","hodgepodge","hogwash","hokum","hoodoo","hoodwink","hooey","hooligan","hoopla","hootenanny","hornswoggle","horsefeathers","hotbed","hotfoot","hothead","hubbub","hullabaloo","humbug","humdinger","humdrum","hunky-dory","hurly-burly","hushpuppy","huzzah","hyperbole","idiom","idiosyncrasies","igloo","ignoramus","impromptu","incognito","incorrigible","incredulous","indomitable","indubitably","infinitesimal","interloper","interrobang","ironclad","izzard","jabberwocky","jacuzzi","jalopy","jamboree","jargogle","jawbreaker","jetsam","jibber-jabber","jink","jitney","jubilee","juggernaut","jujubes","jumbo","junket","juxtaposition","kaleidoscope","kaput","kerfuffle","kerplunk","kibosh","killjoy","kismet","knickerbocker","knickknack","kowtow","kumquat","kvetch","lackadaisical","lagoon","lambasted","lampoon","landlubber","laughingstock","lexicographer","limburger","lingo","loco","loggerhead","logjam","logophile","logorrhea","lollapalooza","lollygag","loofah","loony","loophole","lugubrious","lummox","machinations","madcap","maelstrom","magnificent","majordomo","malapropism","malarkey","manifesto","mastermind","mayhem","mealymouthed","mellifluous","menagerie","miasma","miffed","milquetoast","misanthrope","mishmash","moocher","mojo (also a character in THE MONSTORE)","mollycoddle","mondegreen","moniker","monkeyshines","monsoon","mnemonic","moonstruck","muckety-muck","mudpuppy","mudslinger","muffuletta","mufti","mulligatawny","mumbo-jumbo","murmuration","muumuu","nabob","namby-pamby","nimrod","nincompoop","nitwit","nomenclature","nonplussed","noodge","nudnik","numbskull","onomatopoeia","oomph","orotund","outfox","outlandish","oxymoron","pachyderm","pagoda","palindrome","palomino","panache","pandemonium","pantaloons","papyrus","parabola","parallelogram","parapet","paraphernalia","peccadillo","pedagogue","peewee","pell-mell","persimmon","persnickety","pettifogger","phalanx","phantasmagorical","phantonym","phylactery","piffle","pizzazz","plethora","pogo","pogonip","pollex","pollywog","poltroon","pomposity","poppycock","portmanteau","potpourri","pseudonym","pugnacious","pulchritudinous","pusillanimous","pussyfoot","quibble","quicksilver","quicksticks","quiddle","quinzee","quirky","quixotic","quizzity","rabble-rouser","raconteur","rainmaker","ragamuffin","ragtag","ramshackle","ransack","rapscallion","razzle-dazzle","razzmatazz","rejigger","rendezvous","resplendent","rickrack","ricochet","riffraff","rigmarole","riposte","roundabout","roustabout","rubberneck","ruckus","ruffian","rugrat","rumpus","sabayon","sashay","sassafras","scalawag (also scallywag)","scatterbrain","schadenfreude","schlep","schluffy","schmooze","schmutz","scintillating","scrofulous","scrumdiddlyumptious (Dahlism)","scuttlebutt","serendipity","sesquipedalian","shabang","shenanigans","skedaddle","skirmish","skullduggery","slapdash","slapstick","slipshod","smithereens","smorgasbord","snollygoster","sobriquet","sojourn","spellbind","splendiferous","squeegee","squooshy","staccato","stupefaction","succotash","supercilious","superfluous","surreptitious","Svengali","swashbuckler","switcheroo","swizzlestick","synchronicity","syzygy","talisman","taradiddle","tchotchke","teepee","telekinesis","thingamabob","thingamajig","thunderstruck","tidbit","tintinnabulation","toadstool","toady","tomfoolery","tommyrot","toothsome","topsy-turvy","trapezoid","tub-thumper","tumultuous","typhoon","ululation","umlaut","umpteen","usurp","uvula","vagabond","vamoose","verboten","verisimilitude","vermicious (well, if I included one Dahlism, why not another?)","vertigo","verve","virtuoso","vivacious","vuvuzela","wackadoodle","wallflower","wanderlust","whatchamacallit","whatsis","whimsical","whippersnapper","whirligig","whirlybird","whizbang","whodunit","whoop","widget","wigwam","willy-nilly","windbag","wipeout","wiseacre","wisecrack","wisenheimer","wishy-washy","woebegone","wonky","woozy","wordplay","wordsmith","wunderkind","wuthering","xylophone","yahoo","yokel","yo-yo","zaftig","zeitgeist","zenzizenzizenzic (yes, this is a word!)","zephyr","zeppelin","ziggurat","zigzag","zonked","zoom","zydeco","Bumfuzzle","Cattywampus","Gardyloo","Taradiddle","Snickersnee","Widdershins","Collywobbles","Gubbins","Abibliophobia","Bumbershoot","Lollygag","Flibbertigibbet","Malarkey","Pandiculation","Sialoquent","Wabbit","Snollygoster","Erinaceous","Bibble","Impignorate","Nudiustertian","Quire","Ratoon","Yarborough","Xertz","Zoanthropy","Pauciloquent","Bloviate","Borborygm","Brouhaha","Absquatulate","Comeuppance","Donnybrook","Nincompoop"]


# Function to process each table
def process_table(k, v, table_to_hashes, table_to_IDs, table_to_cache, lock):
    d = v.all()
    with lock:
        table_to_hashes[k] = [elt["id"] for elt in d]
        table_to_IDs[k] = sorted([str(elt["fields"].get("ID")) for elt in d])
        table_to_cache[k] = d

# Initialize dictionaries
table_to_hashes = {}
table_to_IDs = {}
table_to_cache = {}

# Create a lock for thread-safe operations
lock = threading.Lock()

# List to keep track of threads
threads = []

# Start a thread for each table
for k, v in tables.items():
    thread = threading.Thread(target=process_table, args=(k, v, table_to_hashes, table_to_IDs, table_to_cache, lock))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()

# At this point, your dictionaries are populated





# # Authentication function

# Authentication is deactivated by setting DEMO=ON in env vars,
# If authentication is deactivated, the bot will reply to any user
if os.environ['DEMO']=="ON":
    users_scopes={}
    demo_mode=True
    logging.warning("CAUTION! Your bot is not using authentication!")

# if authentication is activated
# retrieve user scopes from airtable
else:
    demo_mode=False
    logging.info("The bot is using aunthentication.")
    
    users_scopes_base_key=os.environ['CHATBOT_USERS_SCOPES_BASE_ID']
    user_table_ID=os.environ['CHATBOT_USERS_SCOPES_table_ID']
    user_scopes_API_key=os.environ['CHATBOT_USERS_SCOPES_API_KEY']
    
    user_table=Table(base_id=users_scopes_base_key,
                     table_name=user_table_ID,
                     api_key=user_scopes_API_key)
    
    users_scopes={}
    for usr in user_table.all():
        usr_name=usr["fields"].get("Telegram link",[""])
        if isinstance(usr_name,str) and len(usr_name)>0:
            usr_name=usr_name.split("/")[-1]
            users_scopes[usr_name]=usr["fields"].get("Scopes",[])





# authentication function
# calling this function as the first line of any I/O function
# makes the bot stubbornly mute to outsiders
def authenticated_user(update, context, scope, users_scopes=users_scopes):
    """Check if user is legitimate and scopes if not in demo mode"""
    
    if demo_mode: return(True)
    
    usr = update.message.from_user.username
    if usr in users_scopes.keys() and scope in users_scopes[usr]:
        logging.info(f"Authenticated_user:{usr}")
        save_chat_id(update,context)
        return(True)
    else:
        logging.warning(f"Non-authenticated_user:{usr}")
        return(False)



def stop(update,context):
    if not authenticated_user(update, context, scope="King"):return(1)
    usr = update.message.from_user.username
    logging.info(f"User {usr} requested bot shutdown.")
    send_msg(update,context,f"OK, give me a moment to reboot.")
    os.kill(os.getpid(), signal.SIGINT)


def save_chat_id(update,context):
    """Saves the chat ID of users interacting with the bot"""
    usr = update.message.from_user.username
    chatID = update.message.chat_id
    
    criteria={"Telegram link":f"https://t.me/{usr}"}
    formula = match(criteria)               
    usr_record = user_table.first(formula=formula)
    user_table.update(record_id=usr_record["id"], fields = {"chatID":str(chatID)})





# # Start, Help, Error functions

# Define standard command handlers. \n",
# These usually take the two arguments update and context.\n",
# Error handlers also receive the raised TelegramError object in error.\n",

def start(update, context):
    """Greet legitimate users and offer quickstart help"""
    if not authenticated_user(update, context, scope="Airtable bot"):return(1)
    send_msg(update,context,f"""
Hi there! 🤓 My mission is to help query any record from our lab Airtable. Click /help for more details.""")
    

def help_msg(update, context):
    """Display summary of how to use the bot"""
    if not authenticated_user(update, context, scope="Airtable bot"):return(1)
    msg = f"""
⭐ Use "/" followed by a record ID to view a record (e.g /dna4303)\n
⭐ The tables you can browse are {", ".join(table_IDs.keys())}. Record IDs are shown in blue, click those to browse the database!\n
⭐ Use "/search" followed by space-separated keywords to search records in the whole database, for instance : /search mScarlet L0"\n
⭐ Use "/timer" with a duration an a description to start a timer, for instance : /timer 10m boil cells.\n
Enjoy"""

    msg=format_ids(msg)
    send_msg(update,context,msg)

def error(update, context):
    """Rather minimal error reporting function""",
    if not authenticated_user(update, context, scope="Airtable bot"):
        return(1)
    logging.warning(f'Update {str(update)} caused error {str(context.error)}')


def timer(update,context):
    
    if not authenticated_user(update, context, scope="Airtable bot"):return(1)
    
    user_time = [elt for elt in update.message.text.split(" ") if not elt.startswith("/")]
    
    if update.message.text=="/timer":
        error_msg='To use the timer send the /timer function followed by space-separated durations. For instance:\n\n /timer 10m 1h 1h 20s boil cells \n\nwill start a timer of 2h 10m 20s called "boil cells".'
        send_msg(update,context,error_msg)
        return(1)
    
    hours=0
    minutes=0
    seconds=0
    
    description = []
    
    for elt in user_time:
        is_duration=False
        if re.match("^[0-9]{1,2}h$",elt):
            hours +=int(elt[:-1])
            is_duration=True
        if re.match("^[0-9]{1,2}m$",elt):
            minutes +=int(elt[:-1])
            is_duration=True
        if re.match("^[0-9]{1,2}s$",elt):
            seconds +=int(elt[:-1])
            is_duration=True
            
        if not is_duration:
            description.append(elt)
    
    if description==[]:
        description="-"
    else:
        description = " ".join(description)

    tot_secs = 60*60*hours + 60*minutes + seconds

    msg = update.message.reply_text("OK, let me start a timer for that.")

    for time_to_wait in range(tot_secs,0,-1):
        sleep(1)
        str_time = str(datetime.timedelta(seconds=time_to_wait))

        msg.edit_text(f"Wait: {str_time} for {description}")

    send_msg(update,context,f"Timer for {description} finished.")

    


# # formatting, sending

def strip_ID_from_message(ID):
    """Format ID (remove slash)"""
    if isinstance(ID,str):
        return(ID.replace("/",""))
    else:
        return(str())


# shitty patch, with a while loop as a bonus
def format_ids(msg):
    """This function formats a message so that known database IDs are displayed with a / prefix. This makes formatted IDs clickable in the chat"""
    for ID_to_recognise in IDs_to_recognise: 
        msg=msg.replace(ID_to_recognise,f"/{ID_to_recognise}")
    
    for ID_to_recognise in IDs_to_recognise: 
        while f"//{ID_to_recognise}" in msg:
            msg=msg.replace(f"//{ID_to_recognise}",f"/{ID_to_recognise}")
    
    return(msg)
        


def split_msg(msg):
    """Split messages larger than 4096 characters into smaller bits (usually before sending)"""

    # catabolism then anabolism ;)
    
    # split at new lines (chew)
    if len(msg)>4096:
        msg = msg.splitlines(True)
    
    # split large chunks further at spaces (digest)
    msg_new=[]
    for elt in msg:
        if len(elt)<4096:
            msg_new.append(elt)
        else:
            for e in elt.split(" "):
                msg_new.append(f"{e} ")
                    
    # rejoin all that into larger pieces (build)
    msg=[]
    tmp=""
    for elt in msg_new:
        if len(tmp)+len(elt)<4096:
            tmp=tmp+elt
        else:
            msg.append(tmp)
            tmp=elt
    msg.append(tmp)
        
    return(msg)


def send_msg(update,context,msg):
    """To send a message to the user"""
    
    if not authenticated_user(update, context, scope="Airtable bot"):
        return(1)
    
    for page in split_msg(msg):
        update.message.reply_text(page,parse_mode=parsemode.ParseMode.HTML)


    threshold = random.random()
    if threshold>0.95:
        update.message.reply_text(f"Also, here's a quote for you:\n\n{random.choice(quotes)}",parse_mode=parsemode.ParseMode.HTML)
    
    elif threshold<0.05:
        funny_word=random.choice(funny_words)
        url=f"https://www.google.co.uk/search?q=what+does+{funny_word.replace(' ','+')}+mean"
        update.message.reply_text(f"""And here's a funny word for you:\n\n<a href="{url}">{funny_word}</a>""",parse_mode=parsemode.ParseMode.HTML)
    
    # increment number of messages sent to user
    usr = update.message.from_user.username
    
    try:
        user_table.update(record_id=usr_record["id"], fields = {"Times used":int(usr_record["fields"]["Times used"])+1})

        criteria={"Telegram link":f"https://t.me/{usr}"}
        formula = match(criteria)
        usr_record = user_table.first(formula=formula)
    except:
        pass
        





# # Keyword search

def get_from_keyword(update,context):
    """Search records in the database using keywords sent by the user. When several keywords are given, they are combined with the AND operator. This is one of the main workers of the bot."""
    
    if not authenticated_user(update, context, scope="Airtable bot"):return(1)

    # sanitize input
    try:
        kwd=str(update.message.text)
        kwd=kwd.replace("/search ","")
        kwd_list=[kwd for kwd in kwd.split(" ") if len(kwd)>0]
        
    except:
        kwd=""
    
    results={}
    # for each table, list IDs that contain keyword in one of the fields to keep
    for table_name in table_to_cache.keys():
        for rec in table_to_cache[table_name]:
            
            keywords_found={k:False for k in kwd_list}
            
            for field_to_keep in fields_to_keep[table_name]+["ID"]:
                r=str(rec["fields"].get(field_to_keep))
                for kwd in kwd_list:
                    if str(kwd).lower() in r.lower(): # case insensitive
                        
                        # save where keyword was found
                        if not isinstance(keywords_found[kwd],list):
                            keywords_found[kwd]=[]
                        keywords_found[kwd].append(field_to_keep)
            
            # if all keywords were found
            if False not in keywords_found.values():
                findings_recap=""
                for kwd,found_in in keywords_found.items():
                    findings_recap=f"""{findings_recap}"<u>{kwd}</u>" (in field(s) {", ".join(found_in)})\n"""
                    
                if table_name not in results.keys():
                    results[table_name]=[]
                results[table_name].append([rec["fields"].get("ID"),findings_recap])
                
    # if too many results (more than 20 for instance) ask user to be more specific
    # and send only the first few results in each table until 20 are shown
    tot_results = sum([len(results[table_name]) for table_name in results.keys()])
    
    # prepare message header
    msg= ' '.join(kwd_list)
    msg=msg.strip()
    msg= f"""{msg}{"🔎 <strong>"+msg+"</strong> 🔎"}\n\n"""
    msg = f"""\n{msg}\n{'─'*20}\n"""
        
    if tot_results>15:
        msg=f"{msg}There are too many results to show ({tot_results}). Please consider using more specific keywords. Showing result IDs only:\n\n"
        
        for table_name in results.keys():
            all_IDs=[]
            for elt in results[table_name]:
                all_IDs.append(f"{elt[0]}") # append ID
            msg=f"{msg}{' '.join(all_IDs)}\n\n"
        
    else:

        for table_name in results.keys():
            for elt in results[table_name]:
                msg = f"{msg}🔹 {elt[0]} from table {table_name}:\n{elt[1]}\n\n"

    msg= format_ids(msg)    

    send_msg(update,context,msg)


# # Hash resolving

# Functions to resolve hashes

# map any hash number to the table (name) that contains it
hash_to_table={}
for table_name,hashes in table_to_hashes.items():
    for hs in hashes:
        hash_to_table[hs]=table_name

# get a record using its hash and table of origin
def get_record_from_hash(hs):
    """Get record associated to a hash"""
    table_name=hash_to_table[hs]
    table = tables[table_name]
    rec = table.get(hs)
    return(rec)

def get_ID_from_HASH(hs):
    """Get human readable ID of the record associated to a hash"""
    record = get_record_from_hash(hs)
    ID =record["fields"].get("ID",hs)
    return(ID)

def hash_mapper(cell,verbose=False):
    """Replace single hashes or lists of hashes by human readable IDs"""
    if isinstance(cell,list):
        new_cell =[get_ID_from_HASH(hs) if hs.startswith("rec") else hs for hs in cell]
    else:
        new_cell=cell
    
    return(new_cell)


# # Fetch record info function

def field_is_attachment(table_name,field_name,record):
    # check if the field is found
    the_field = [field for field in table_schemas[table_name].get("fields") if field.get("name")==field_name]
    if the_field:
        the_field=the_field[0]
    else:
        msg="Unknown field"
        logging.error(msg)
        return(msg)

    # check field type
    the_field_type = the_field.get("type")

    if the_field_type=='multipleAttachments':
        return(True)
    else:
        return(False)





def prepare_field_for_message(table_name,field_name,record):
    """Prepares the contents of a field for printing, taking its type into account"""

    # check if the field is found
    the_field = [field for field in table_schemas[table_name].get("fields") if field.get("name")==field_name]
    if the_field:
        the_field=the_field[0]
    else:
        msg="Unknown field"
        logging.error(msg)
        return(msg)

    # check field type
    the_field_type = the_field.get("type")

    # format URLs
    if the_field_type=='url':
        url = record.get("fields").get(field_name)
        formatted_url = f"""<a href="{url}">Link</a>"""
        return(formatted_url)

    # format multipleSelects
    elif the_field_type in ['multipleSelects','multipleLookupValues']:
        return(", ".join(record.get("fields").get(field_name,list())))

    # format multipleRecordLinks (this handles also link fields linked to max 1 record)
    elif the_field_type=='multipleRecordLinks':
        record_links=record.get("fields").get(field_name)
        if record_links:
            human_readable=hash_mapper(record.get("fields").get(field_name))
        else:
            human_readable=list()
        
        if human_readable:
            human_readable=", ".join(human_readable)
            
        return(human_readable)
    

    # format singleLineText 
    elif the_field_type in ['singleLineText','richText','singleSelect','formula']:
        
        return(record.get("fields").get(field_name))

    elif the_field_type=='currency':
        value=record.get("fields").get(field_name)
        symbol=the_field.get('options',{}).get('symbol',str())
        return(f"{value} {symbol}")

    elif the_field_type=='multipleCollaborators':
        
        if isinstance(record.get("fields").get(field_name),list):
            names = [elt.get("name") for elt in record.get("fields").get(field_name)]
            return(", ".join(names))
        if isinstance(record.get("fields").get(field_name),dict):
            return(record.get("fields").get(field_name).get('name'))

    # format attachments
    elif the_field_type=='multipleAttachments':
        return('multipleAttachments')

    else:
        try:
            return(str(record.get("fields").get(field_name)))
        except:
            return("Could not format contents")
        

    
    print(record.get("fields").get(field_name))





# Main function to fetch and send record information

def get_record_data(update,context,ID,table_name):
    """Get data associated to a human readable ID in the table called "table_name", format it with a lot of emojis and send the info to the user. This is one of the main workers of the bot."""
    if not authenticated_user(update, context, scope="Airtable bot"):
        return(1)
        
    criteria={"ID":ID}
    formula = match(criteria)
    result = tables[table_name].first(formula=formula)
    
    # get previous and next IDs in the table
    try:
        previous_ID = table_to_IDs[table_name][table_to_IDs[table_name].index(ID)-1]
    except:
        previous_ID=table_to_IDs[table_name][-1] # so we can browse records as a loop
        
    try:
        next_ID = table_to_IDs[table_name][table_to_IDs[table_name].index(ID)+1]
    except:
        next_ID =table_to_IDs[table_name][0] # so we can browse records as a loop
    
    msg=f"""👩‍🔬🧪🧫🧬🦕 <strong>{ID}</strong> 🔬💉🦠🖥️👨‍🔬\n"""
    msg = f"""\n{msg}\n{'─'*20}\n"""

    
    for field_to_keep in fields_to_keep[table_name]:
        r=result["fields"].get(field_to_keep,False)
                
        # if the field to keep contains some info, do stuff
        if r:

            if field_is_attachment(table_name,field_to_keep,result):
                 # retrieve attachment and send it
                try:
                    url=result["fields"].get(field_to_keep)[0].get("url")
                    file_name = result["fields"].get(field_to_keep)[0].get("filename")
                    for extension in ["jpg","jpeg","png","svg"]:
                        if extension in str(result["fields"].get(field_to_keep)[0].get("type",str())).lower():
                            break
                    if not file_name.endswith(extension):
                        file_name=f"{file_name}.{extension}"
                    file_path = str(working_dir/f"{file_name}")
                    subprocess.run(["wget",url,"-O", file_path])
                    if extension=="svg":
                        
                        drawing = svg2rlg(file_path)
                        file_path=file_path.replace("svg","png")
                        renderPM.drawToFile(drawing,file_path, fmt='PNG')
                    updater.bot.send_document(chat_id=update.message.chat_id, document=open(file_path, 'rb'))
                except:
                    logging.exception("Could not send attachment")
                    
            else:
                formatted = prepare_field_for_message(table_name,field_to_keep,result)
                formatted=formatted.strip()
                if not formatted:
                    formatted="-"
                msg=msg+f"""\n\n<strong>🔹 {field_to_keep} </strong>: {formatted}"""
    
    # adding previous/next record links
    msg = f"""\n{msg}\n{'─'*20}\n"""
    msg = f"""{msg}⬅️ {previous_ID} - {next_ID} ➡️"""
    
    # format IDs for interactive clicking
    msg = format_ids(msg)

    # prettify #xxx
    while "\n"*3 in msg:
        msg=msg.replace("\n"*3,"\n"*2)

    
    
    
    # and send !
    send_msg(update,context,msg)
        
    return(0)

# note : comments in rich text format seem to crash the script for some reason
# probably related to the presence of URLs in the comments.


# # Fetch record with weird ID function

# some functions to look for unusual IDs

def get_weirdID_data(update,context,ID):
    """If the table to which belongs the ID requested by the user can not be easily guessed using its prefix, this function searches for the ID in each table of the database. This can resolve non-standard IDs for instance the backbone called pICH47781 and also catches stupid names, for instance a genome that would be called primer_4444."""

    if not authenticated_user(update, context, scope="Airtable bot"):
        return(1)

    # first determine in which table to look
    # then redirect to the appropriate function
    table_found=str()
    for tabe_name,table_IDs in table_to_IDs.items():
        if ID in table_IDs: # if the weird ID is found in the list of IDs from this table, this is the table
            table_found=tabe_name
            break
    if table_found:
        get_record_data(update,context,ID,table_found)
    else:
        msg="Could not find the record, sorry. Does a record with this name exist in the base? Is the table that contains it indexed? Is the ID of the record short enough? And without spaces?"
        send_msg(update,context,msg)


# diverse error messages
custom_error_messages={}


# # Shortcut function

def fetch_and_return_info(update, context):
    """This function is here to speed up the search of the ID requested by the user
    by looking first into the expected table. 
    So for instance, upon receiving an ID starting with "mol" 
    this function will start looking for the corresponding record in table M. 
    If this fails, the ID is passed to the function get_weirdID_data, 
    which is much slower. In short: use consistent naming."""
    
    if not authenticated_user(update, context, scope="Airtable bot"):
        return(1)
    
    ID = strip_ID_from_message(update.message.text)

    table_name = str()
    if ID.startswith("data_") :table_name="Exp"        
    elif ID.startswith("ptcl"):table_name="Protocols"
    elif ID.startswith("dna"):table_name="C"
    elif ID.startswith("mol"):table_name="M"
    elif ID.startswith("gnm"):table_name="Genomes"
    elif ID.startswith("str"):table_name="Str"
    elif ID.startswith("gly"):table_name="Gly"
    elif ID.startswith("gg"):table_name="GG"
    elif ID.startswith("primer_"):table_name="Primers"
    elif ID.startswith("pcr"):table_name="PCRs"
    elif ID.startswith("comp"):table_name="CompetentCells"
    elif ID.startswith("bkb"):table_name="Backbones"

    else:
        pass

    if table_name:
        criteria={"ID":ID}
        formula = match(criteria)               
        result = tables[table_name].first(formula=formula) # this is the problem
        if len(result):
            get_record_data(update,context,ID,table_name)
    else:
        msg="This ID does not seem to match a known format. Please wait a moment while I search it in the base."
        send_msg(update,context,msg)
        get_weirdID_data(update,context,ID)
        
        


# # timer function

def timer(update,context):
    if not authenticated_user(update, context, scope="Airtable bot"):return(1)
    
    user_time = [elt for elt in update.message.text.split(" ") if not elt.startswith("/")]
    
    if update.message.text=="/timer":
        error_msg='To use the timer send the /timer function followed by space-separated durations. For instance:\n\n /timer 10m 1h 1h 20s boil cells \n\nwill start a timer of 2h 10m 20s called "boil cells".'
        send_msg(update,context,error_msg)
        return(1)
    
    hours=0
    minutes=0
    seconds=0
    
    description = []
    
    for elt in user_time:
        is_duration=False
        if re.match("^[0-9]{1,2}h$",elt):
            hours +=int(elt[:-1])
            is_duration=True
        if re.match("^[0-9]{1,2}m$",elt):
            minutes +=int(elt[:-1])
            is_duration=True
        if re.match("^[0-9]{1,2}s$",elt):
            seconds +=int(elt[:-1])
            is_duration=True
            
        if not is_duration:
            description.append(elt)
    
    if description==[]:
        description="-"
    else:
        description = " ".join(description)

    tot_secs = 60*60*hours + 60*minutes + seconds

    msg = update.message.reply_text("OK, let me start a timer for that.")

    for time_to_wait in range(tot_secs,0,-1):
        sleep(1)
        str_time = str(datetime.timedelta(seconds=time_to_wait))

        msg.edit_text(f"Wait: {str_time} for {description}")

    send_msg(update,context,f"Timer for {description} finished.")

    





# # Start bot

updater = Updater(TOKEN, use_context=True)

dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_msg))
dp.add_handler(CommandHandler("search", get_from_keyword)) # ,run_async=True 
dp.add_handler(CommandHandler("timer",timer,run_async=True))
dp.add_error_handler(error)


if not demo_mode:
    updater.dispatcher.add_handler(CommandHandler('stop', stop))
    # allowing some users to stop the bot only when auth is active


# add command handlers iteratively from all IDs in airtable...
# Note : the creation of handlers fails when the ID is too long or contains spaces
IDs_to_recognise=[]
for k,v in tables.items():
    for record in tables[k].all():
        try:
            # note here that IDs containing a "&" or a space (or other stuff apparently) crash the creation of handlers...
            readable_ID = record["fields"].get("ID")
            dp.add_handler(CommandHandler(readable_ID, fetch_and_return_info,run_async=True))
            # save IDs to recognise and format in messages. At least those that passed the previous line ;)
            IDs_to_recognise.append(readable_ID)
        except:
            # report IDs that fail to create a handler. Those will not be clickable by the user
            # they are mercifully few of them, but most of them affect backbones, whose IDs are quite diverse
            logging.error(f"Table {k}: creation of handler {readable_ID} failed ({record['id']},{record.get('fields').get('ID')})")
            
# rather basic way to make sure that longer IDs containing shorter IDs 
# (for instance "mol511" containing "mol51")
# do not get split/over-written when formatting IDs for interactive clicking
IDs_to_recognise = sorted(IDs_to_recognise, key=len)
IDs_to_recognise=list(reversed(IDs_to_recognise))


updater.start_polling()
updater.idle()










