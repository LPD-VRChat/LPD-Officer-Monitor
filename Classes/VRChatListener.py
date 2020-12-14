import vrcpy
import asyncio
from time import sleep as sleep
from termcolor import colored
from datetime import datetime, timezone
loop = asyncio.get_event_loop()
client = vrcpy.Client(loop=loop)

def printd(string):
    timestamp = (str(datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")))
    string = colored(timestamp, 'magenta') + ' - ' + string
    print(string)


async def main(username, password):
    await client.login(
        username=username,
        password=password
    )
    #loop.create_task(keep_alive())
    try:
        # Start the ws event loop
        await client.start()
    except KeyboardInterrupt:
        await client.logout()

async def start(username, password, Bot):
    loop.create_task(main(username, password))
    global bot
    bot=Bot

async def stop():
    await client.logout()

@client.event
async def on_friend_location(friend_b, friend_a):
    world_name = await client.fetch_world_name_via_id(friend_a.world_id)
    instance_number = friend_a.instance_id.split('~')[0]
    if instance_number == 'private':
        world_string = colored('a Private World', 'yellow')
    else:
        world_string = colored(world_name, 'yellow') + '#' + instance_number
    printd("{} is now in {}".format(colored(friend_a.display_name, 'green'), world_string))
    officer_id = bot.user_manager.get_discord_by_vrc(friend_a.display_name)
    officer = bot.officer_manager.get_officer(officer_id)
    if officer.is_on_duty:
        vrc_name = friend_a.display_name
        enter_time = datetime.now(timezone.utc)
        avatar_image_url = friend_a.avatar_image_url
        allow_avatar_copying = friend_a.allow_avatar_copying
        await bot.officer_manager.send_db_request(f"INSERT INTO VRChatActivity (officer_id, vrc_name, world_name, instance_number, enter_time, avatar_image_url, allow_avatar_copying) VALUES ({officer_id}, '{vrc_name}', '{world_name}', '{instance_number}', '{enter_time}', '{avatar_image_url}', {allow_avatar_copying})", None)
        print('is on duty')
    
async def save_officer_location(officer_id):
    vrc_name = bot.user_manager.get_vrc_by_discord(officer_id)
    user = await client.fetch_user_via_id(vrc_name + '/name')
    world_name = await client.fetch_world_name_via_id(user.world_id)
    instance_number = user.instance_id
    enter_time = datetime.now(timezone.utc)
    avatar_image_url = user.avatar_image_url
    allow_avatar_copying = user.allow_avatar_copying
    await bot.officer_manager.send_db_request(f"INSERT INTO VRChatActivity (officer_id, vrc_name, world_name, instance_number, enter_time, avatar_image_url, allow_avatar_copying) VALUES ({officer_id}, '{vrc_name}', '{world_name}', '{instance_number}', '{enter_time}', '{avatar_image_url}', {allow_avatar_copying})", None)




@client.event
async def on_friend_active(friend_a):
    if friend_a.state == 'online':
        await on_friend_online(friend_a)
        return
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), friend_a.state))


@client.event
async def on_friend_online(friend_a):
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), colored('online', 'cyan')))


@client.event
async def on_friend_add(friend_b, friend_a):
    printd("{} is now your friend.".format(colored(friend_a.display_name, 'green')))


@client.event
async def on_friend_delete(friend_b, friend_a):
    printd("{} is no longer your friend.".format(colored(friend_a.display_name, 'green')))


#@client.event
#async def on_friend_update(friend_b, friend_a):
#    printd("{} has updated their profile/account.".format(colored(friend_a.display_name, 'green')))


#@client.event
#async def on_notification(notification):
#    printd("Got a {} notification from {}.".format(
#        notification.type, notification.senderUsername))


@client.event
async def on_connect():
    printd("Connected to wss pipeline.")
    #await add_friend()

@client.event
async def on_disconnect():
    printd("Disconnected from wss pipeline.")

async def join_user(user_id):
    user = await client.fetch_user_via_id(user_id)
    join_link = 'vrchat://launch?' + user.location
    return join_link
    
async def send_invite(user_id):
    user = await client.fetch_user_via_id(user_id)
    join_link = 'vrchatL//launch?' + user.location
    return join_link

async def keep_alive():
    while True:
        me = await client.fetch_me()
        sleep(300)

async def add_officer_as_friend(vrc_name):
    user = await client.fetch_user_via_id(vrc_name + '/name')
    await user.send_friend_request()


async def add_friend():
    friends_list = """Smile_미소;Piscess;100chilly;MissNerdyCandy;PhantomGR;Plymouther;Raicher;j11;OpWolf;Midori Sapphire;digikind;Reeva_VR;ZTwoTL;Nathanimall;DonnEStarside;darkwingedninja;Houdini111;Netsu Greyfang;Nova4Dayz;MoguTheBogu;dmx512;The․Game;Sukadia;Canesfan56;DaCupNoodlez;AliceD;Ruri Kotohime;ThatOneKray;Seras_;HACKhalo2;AFoulXzeno;Deltaos;RoboticAlienDude;FeiLi-緋璃;Summerman123;Pixel Nocturnus;DrCheesebuger;Moon Trash 2000;Karet;Delayed;トキドキ;aSupremeSloth;Jones26;MisFitUltra;TachankaL0rd;Mushiiii;Lurkerus;TheBluePotato;Sniperzero112;Pierce__;Taiga Tm;Bishonen;thomatoes50;FoxGods;Flonnezilla;Dorothy Haze;Sunny ≻˸3;SiggyZ;austinrisepic;ExoAssassin;EmeraldGemini96;Raizig;Capitalism_chan;sashlilac34;Nautis;NeoValentine;Saebeltiger;Jesudere;coolcolinc;7‒Eleven;Notshane;HoppyS;reginald123456;Im_Tomoya;Paintably;Detective Eevee;marcuzfenexkungfu;wiipetsto;Νeptunə;DarkSaito;MrDolphin;TheGamingExite;HachiDog;TacticianRobin;Ysmir-m;haru_nene;Dakayto;mowsterowo;CecilyJisi;竹奈卿子;CoolCat2017;Hope_tm;thisscreenisnut;JINA1745;✠DashyDragneel✠;DarkSoulitude;Suklo;SebassTehFish;wolfieboy762;DivineLiberty;Ecclesia;Kayla~‎;Screeble;gunner190;Neptune_;PeachLord;たかなし みつき;Sharpyy;Harithan;saintofwar3;TheMaddog;UberKnight;Dyllersen;RookieRanger;HappyCorgi;ᅳ;Walactor;KuroFoxYokai;Chris_Kani;4Hani;aboxofpeanuts;RisuFortunae;MKKelvinHK;NeonicBlueStar;M200chan;DerpiCat;Markurion;Cap Destructo;Killswig;DrillSargeKris;Battlyz;DoodleStarr;Blue Angel 97;IMikkachuI;silentnightz;choyberg;Ozhy;Corbantis;PurpleGhost;corvus_corax137;namesvale;NormanSF［1572］;Kitra;poggersFisch;Mysticzizu;NEBUR650;nico445e;blubvis;Blue Cookie;Sgt․ Nowak;ShyBlakey＆Mochi;LycanRoses;JoyfulDemon01;MUDDKING;Kilroy_22;IDarky 212B;Nyaaaaaaaa;GalaxyPrime;flyineko｜假飞猫;Jeaver;Burezu;MoeKitsune;∗ART∗;Meneria Brot;AtomicPage;SSG․ Gaz;Psychic320;Olly 4104;THE_RAMKILLER;Molls;csisson6101;boxxkitt;Aelic211;SantaFIP;DarkSpookyTuna;Acari;Tomato-God;ポルトー;Nature Sounds;BunnyMinx;Tooweeb;Orazzy;PinHead720;Faithexx;Kreme-;NebuIa;✰Joey✰Joestar✰;FairDinkumDave;AstralPrototype;Vinnoe;Insanitorium9;Jagalon;aetaswho;Cheryone;Admiral_Johnson;Tron_woof;WOOLFIE_;MangeDesEpinard;≺FriendlyNPC≻;Sierra_Paro;yujin0405꿻뚧쒧맭;Ninja_taro;qxtell;Monerasius;The_w0lf;Tomnautical;Milo Moon;Kohai~Senpai;AviatorNic28;rykllan;Rusty AK47;RedArrowBD;Pz․Grenadier 19;Arctic Fennec;Ｆａｗｋｅｓ;JunkieCS;Yutas;MilitaryDreamer;chillycarlson;ToWeird;Intergalactic;_37__;DarkWolfyChan;Unlitrooper;viperwater;Frisman;Vuel Blackberry;trisihd;Andycai23;사이버 （Cyber）;MK12 MOD1;galaxydragon50;AllGamesBlazing;Sazbadashie;ユィゥナ（ＬＩＮ）;Nootles;noobs24;DataMcLP;Grisly53;Dono;Rezzna;Jamesluner;［InsertText］;Monolith_CK;SquareDorito;Tesla-7;Dice3Sides;_Tzar_;SteelSnake925;HTI4U☆Blue;the destroyer;A096k_Sky;Drak［드렉］;MashiroQAQ;Königstiger;Averimon;KarmaDiya;commanderPUG212;Kashikuzi;♡MilkLink♡;BREADYOLK;4inchLoli;Yuuto666;nier_;symphonybreeze;Lynnikai;Ponyo_1;qWeR1111;Alli3Gal;Worthiツ;Dark_shadow97;The Butters;CoffeeeVR;Emperor_calus;Joesh;ThePaleMale;Cheef_Teef;TheExtra;DJ-G6PON3;Hroi;wellfire;MollyBug;Quigleyyy;An Average Weeb;ShadowMJ;ṨҤ¥-ƘU₦;AstronautSniper;ODST162;RedAlphaTails;Phantom309;Tails115;1NIGHTMAREGAMER;KadenTGM;RXXTD;Daikei;bakedpotato4;Schwi_dola;Locadia;Nightwisp;Dorinio;Khangaluwu;SuduckaDim;Daylizard24;Hartman Nix;․~Senpai~․;TeeJ~;虛無神龍;Nervig2001;K_Dempsey;Gypzyfire;ROB_22;clooud;TheGam1ngFox;Lord of Avernus;Afroking;․YUKI SCARN․;Sulliver;ShinoNova;MCFeelBoy;Stoffiboii;Daddy'sKitten;․hols․;IzDaPeanut;CptKkz_Natsuki;Violent Scot;＝RUAA＝;fr0stsh4dow;-littledog-;FoxOfSalvation;CoreGamer;PuddingTH;Zharthumil;IIZOMBIESHOOTII;Magister11;UMP45․;j3st3r;Tya-han;Ookami Sensei;dark resin;warabi0825;CEO of Hell;Lego14;Advanced Derp;ntpandorax;zipey uwu;Axi0m_;TheFoxyDemon;WickedFlyGirl;Pr3ttyLPsych056;saitamastrength;VIP_Sheriff;ericirno;Ginger Tea;Komondor_O․G;Solfiken;Nox_ノクス;Kaori_01;nary＆89;oliew;Shadow_Cascad3;Nekomanz;Bzlongshotz;onemorechocobo;Senk0San;Poppskey;StarLitLady;IInco;_-DeadSoul-_;PlushyMarshmallow;Izuna-chan;＾_＾Longleggs＾_＾;SixHasTricks;AlmightyConman;Agaki;KProsen4;Th3AegisBlade;Lokı;WolfNinja9;VT_Hirosuke;咸鱼の王者Dream;Zipperman;power of felix․;MadlessHatter;EternalAlex;Tris˸ NEET LORD;TheDillyDilly;Kim slow;Gabriel-White;Kanokochan;YatsumeBaka;Stridenttugboat;Galahad™;catattack551;Jasson;OFFICER495;이재민 （HK416）;HeatWarrior546;Grombindal;Manemana;KongP;Nayubi;Mizugaiya;TAXIdriver200;transwoman18;OG lone scout;Iris_2184;❤ NekoSenpai ❤;zerotwo9;butterpixie;黑杰克-杰哥;JavaPROx;Inkypee;MCRanger;Lon3lyMoonLight;MagmaNyx;jneko;HK-Hunter404;RoccoKun~;Mocha Amour;midnyt_shadow;pomelly;夜嵐蝶Alma;DC_Puff_TW;安安kgkr;Flute빌런;mad_pickachu;devilsguy1;NasalBone;02-GGod;Remilia Moon;Akumiś;Nep_Nep17;火焰之 迅;Minto_vrc;LilMikeey;轻描淡写;Meko_Chan;Koto_zeo;5Ocent;X․․․x 4e 6f 21;Tacctfull;tonayee;NightCore R;AshleahXD27;TQNF;The decE1ver;LunarTree304;GovekGono;TyroneTyrone;NekoYashA＠桜奈美樹;JF233（疾风）;speeder2621;幻想乡酋长;Alva Meyer;Duck_Duck_Goose;Knight Niron;Penny_Nashdu;FeldwebeIRudi;Metatroni;红Lotus;SwagkillerB;Banshee1;チウ・インリ;Mashrio;CocaCola233;无聊BOOM_XD;btaotaotao;Maverick483;❀ Zinnia ❀;tootherelm;_Strawberry;Nigeki;Cam The Kid;․Lunaberry․;SiniYuna;Somalia ุ;AlphaVer;Killswitch17;Cocoǃ;Xerces;Étsitra the Cún;PVTGhostly76;TheFlashBat;Shyvian;Bloodeye Gamer;certified_loli;sdyu;Churmite;TheMetrocop;teteri;CookieChan20;AspectSteels;Renard［Trans］;Cpt․CrazyMuffin;MAX011;Sunny Skies;Chaplin Death;lilnoodledragon;Jesus115;Mad Max;Cereal_Lain;NateAllCodey;FluffyVibez;yurybird;Da1ister;․The Phoenix․;お菓子マン;Challenge_VRC;deepwebanime;八雨Hachiame;Robertcop;_suki;RainWoofWoof;Fadezzz;NigelBoswell006;_Newt;AmourVR;Feloria;Kalesy;BLIZZ2012;Liftoff22;NovaPandora;That-hectic-guy;Stellmo;Kito_The_Bean;SCPGuRong"""
    for user in friends_list.split(';'):
        UserToFriend = client.fetch_user_via_id(user + '/name')
        await UserToFriend.send_friend_request()
        sleep(60)
        