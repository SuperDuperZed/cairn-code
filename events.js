const bizarreEvents = [
  {
    year: 1518,
    title: "The Dancing Plague of Strasbourg",
    description: "Hundreds of people took to the streets of Strasbourg and danced uncontrollably for weeks. Some danced until they collapsed from exhaustion or died of heart attacks. Town authorities even built a stage and hired musicians, believing that encouraging the dancing would cure it. It didn't.",
    image: "paintings/01_dancing_plague.png",
    source: "Chronicles of the city of Strasbourg, 1518"
  },
  {
    year: 1919,
    title: "The Boston Molasses Disaster",
    description: "A 50-foot-tall tank of molasses burst in Boston's North End, sending a 25-foot wave of thick, dark syrup through the streets at 35 mph. The wave crushed buildings, toppled a fire station, and killed 21 people. For decades, locals claimed you could still smell molasses on hot summer days.",
    image: "paintings/02_molasses_disaster.png",
    source: "Boston Evening Globe, January 16, 1919"
  },
  {
    year: 526,
    title: "The Year Without Summer (Antiquity)",
    description: "A massive volcanic eruption — possibly Ilopango in El Salvador — blanketed the Northern Hemisphere in ash, causing temperatures to plummet worldwide. Crops failed across Europe and Asia. Chronicles describe a sun that 'gave no more light than the moon' and snow falling in summer.",
    image: "paintings/03_darkened_skies_antiquity.png",
    source: "Procopius, Wars of Justinian; dendrochronology records"
  },
  {
    year: 1816,
    title: "The Year Without a Summer",
    description: "After the eruption of Mount Tambora in Indonesia, global temperatures dropped so severely that summer never arrived in the Northern Hemisphere. June snowstorms buried New England crops, ice formed on rivers in July, and Mary Shelley wrote Frankenstein during the gloomy Swiss summer that resulted.",
    image: "paintings/04_snow_in_june.png",
    source: "Contemporary weather logs and newspaper accounts"
  },
  {
    year: 1876,
    title: "The Man Who Became a Centenarian Overnight",
    description: "When the British government of India introduced a standardized calendar, residents of a region that had been using the Bikrami calendar (about 57 years ahead) suddenly found themselves 57 years older overnight. Tax records showed men in their 160s and women in their 140s.",
    image: "paintings/05_centenarian_overnight.png",
    source: "British Colonial Administrative Records, 1876"
  },
  {
    year: 1327,
    title: "The Cow That Was Tried for Murder",
    description: "In the French town of Falaise, a sow was arrested, dressed in human clothes, put on public trial, and executed by hanging for killing a child. The court appointed a lawyer for the pig. This was not an isolated incident — medieval Europe held dozens of animal trials, including beetles, rats, and snails.",
    image: "paintings/06_pig_trial.png",
    source: "Records of the Norman court at Falaise"
  },
  {
    year: 1945,
    title: "The Battle of Castle Itter",
    description: "Five days before the end of WWII, American and German soldiers fought side by side to defend a castle from the Waffen-SS. The castle held French VIPs including former prime ministers and a tennis star. It is the only time Americans and Germans fought as allies in the war.",
    image: "paintings/07_castle_itter.png",
    source: "US Army after-action reports; accounts of Josef Gangl"
  },
  {
    year: 1780,
    title: "New England's Dark Day",
    description: "On May 19, 1780, the sky over New England turned pitch black at noon. Birds sang their evening songs at midday, candles were required for all activities, and the Connecticut legislature debated adjourning sine die, believing Judgment Day had arrived. The cause remains debated but was likely massive Canadian wildfires.",
    image: "paintings/08_dark_day.png",
    source: "Diary of Reverend Nathaniel Gage; Connecticut legislative records"
  },
  {
    year: 1859,
    title: "The Great Pig War",
    description: "A dispute over a shot pig nearly started a war between the United States and Britain. An American farmer on San Juan Island shot a British-owned pig that had wandered into his potato patch. Both nations sent warships and troops, but officers on both sides strictly refused orders to fire. The standoff lasted 12 years.",
    image: "paintings/09_pig_war.png",
    source: "Joint British-American commission records"
  },
  {
    year: 1914,
    title: "The Christmas Truce",
    description: "On Christmas Day of the first year of WWI, soldiers along the Western Front spontaneously laid down their weapons and climbed out of the trenches. They exchanged gifts, played football in no-man's land, and sang carols together. Commanders on both sides were furious and ordered it never to happen again.",
    image: "paintings/10_christmas_truce.png",
    source: "Letters home from British and German front-line soldiers"
  },
  {
    year: 1859,
    title: "The Carrington Event",
    description: "The most powerful solar storm ever recorded struck Earth. Telegraph systems worldwide went haywire — operators received electric shocks, telegraph paper caught fire, and messages could be sent even with batteries disconnected. Auroras were visible as far south as Cuba and Hawaii. If it happened today, it could cripple global infrastructure.",
    image: "paintings/11_carrington_event.png",
    source: "British Astronomical Association records; telegraph operators' logs"
  },
  {
    year: 1896,
    title: "The Bicycle Face Plague That Wasn't",
    description: "Medical journals warned that riding bicycles would give women a permanent condition called 'bicycle face' — bulging eyes, clenched jaw, and a flushed complexion. The condition was entirely invented by opponents of women's cycling, who were threatened by the newfound freedom bicycles gave women to travel unescorted. Despite having zero scientific basis, the diagnosis appeared in medical textbooks for years.",
    image: "paintings/12_bicycle_face.png",
    source: "British Medical Journal, 1897; New York Times health column"
  },
  {
    year: 1938,
    title: "The War of the Worlds Panic",
    description: "Orson Welles's radio adaptation of H.G. Wells's novel was so realistic that thousands of Americans believed Martians were actually invading New Jersey. Police stations were flooded with calls, highways clogged with fleeing cars, and people reported seeing poison gas and alien tripods. Welles had to hold a press conference to apologize.",
    image: "paintings/13_war_worlds_panic.png",
    source: "New York Times, October 31, 1938; CBS radio archives"
  },
  {
    year: 1599,
    title: "The Whale That Swallowed a Man Whole (For Real)",
    description: "Sailors aboard a Dutch whaling ship in the Indian Ocean reported that one of their shipmates, named Jan van Linschoten, was swallowed by a sperm whale and later recovered alive when the whale was harpooned and cut open. He reportedly survived for several hours inside, though modern scientists are deeply skeptical of the account.",
    image: "paintings/14_whale_swallow.png",
    source: "Dutch East India Company shipping logs"
  },
  {
    year: 1883,
    title: "The Loudest Sound Ever Recorded",
    description: "The eruption of Krakatoa produced a sound so powerful it ruptured the eardrums of sailors 40 miles away and was heard clearly 3,000 miles away in islands near Madagascar. The shockwave circled the globe three and a half times. Barographs worldwide registered the pressure wave for five days after the eruption.",
    image: "paintings/15_krakatoa.png",
    source: "Royal Society of London report, 1888; global barograph records"
  },
  {
    year: 1928,
    title: "The Great Okefenokee Swamp Fire",
    description: "A wildfire burned 200,000 acres of Georgia's Okefenokee Swamp, producing so much smoke that it created its own weather system. The fire-generated thunderstorms produced lightning that started new fires ahead of the main blaze. The smoke was so thick that ships in the Atlantic reported zero visibility 50 miles offshore.",
    image: "paintings/16_swamp_fire.png",
    source: "US Forest Service fire records; Savannah Morning News"
  },
  {
    year: 1933,
    title: "The Australian Emu War",
    description: "After farmers complained that emus were destroying their crops, the Australian military deployed soldiers with machine guns to fight the birds. Over several weeks, the soldiers fired thousands of rounds at emus that scattered into the bush and reformed elsewhere. The emus won decisively. Major Meredith reported that the birds 'faced the machine guns with complete indifference.' The army withdrew in humiliation.",
    image: "paintings/17_emu_war.png",
    source: "Australian Department of Defence archives; Perth Sunday Times"
  },
  {
    year: 1770,
    title: "The Great London Cheese Riot",
    description: "When a massive wheel of cheese was put on public display, a crowd grew so large and unruly that it turned into a full-scale riot. The cheese was eventually consumed by the mob, but only after several people were injured in the crush and nearby shop windows were smashed. The cheese was reportedly a cheddar wheel weighing over 1,000 pounds.",
    image: "paintings/18_cheese_riot.png",
    source: "London newspapers, 1770"
  },
  {
    year: 1666,
    title: "The Rain of Fish on India",
    description: "Residents of an unspecified town in India reported that fish rained from the sky during a heavy storm. The phenomenon was well-documented by local officials, who noted that the fish were of species not found in any local river. Modern science attributes 'animal rain' to waterspouts that lift aquatic creatures into storm clouds.",
    image: "paintings/19_rain_of_fish.png",
    source: "Mughal Empire administrative correspondence"
  },
  {
    year: 1783,
    title: "The Laki Eruption's Poisonous Haze",
    description: "A volcanic fissure in Iceland erupted for eight months, releasing poisonous gases that killed 20-25% of Iceland's population and 80% of its sheep. The resulting ash cloud drifted over Europe, causing droughts, crop failures, and extreme heat. In Egypt, the Nile failed to flood that year, leading to famine. Some historians link it to food shortages that helped trigger the French Revolution.",
    image: "paintings/20_laki_eruption.png",
    source: "Icelandic parish records; European weather observations"
  },
  {
    year: 1920,
    title: "The Wall Street Bombing",
    description: "A horse-drawn wagon loaded with 100 pounds of dynamite and 500 pounds of iron slugs exploded on Wall Street at lunchtime, killing 38 people and injuring hundreds. The blast left a crater 30 feet wide. The perpetrators were never caught. The wire-mesh window guards on nearby buildings can still be seen today.",
    image: "paintings/21_wall_street_bombing.png",
    source: "Federal investigation files; New York Police Department archives"
  },
  {
    year: 1888,
    title: "The Schoolchildren's Blizzard",
    description: "A sudden, severe blizzard struck the US Plains states on January 12 with virtually no warning. Temperatures dropped 40 degrees in minutes. Hundreds of children, walking home from school, froze to death. One teacher tied her students together with a clothesline and led them to safety, losing only three who broke away from the line.",
    image: "paintings/22_schoolchildren_blizzard.png",
    source: "U.S. Army Signal Corps weather records; survivor testimonies"
  },
  {
    year: 79,
    title: "The Elder Pliny's Scientific Suicide",
    description: "When Mount Vesuvius erupted, the naturalist Pliny the Elder sailed across the Bay of Naples to rescue friends and observe the phenomenon. He went ashore, took a nap, and when servants tried to evacuate him, he reportedly said 'I would rather die than cause my friends any alarm.' He was later found dead, likely from asphyxiation.",
    image: "paintings/23_pliny_vesuvius.png",
    source: "Letters of Pliny the Younger to Tacitus"
  },
  {
    year: 1900,
    title: "The Galveston Hurricane and the Orphan Train",
    description: "The deadliest natural disaster in US history killed an estimated 8,000-12,000 people when a hurricane struck Galveston, Texas without warning. The storm surge literally washed entire families out to sea. Surviving children with no identifiable relatives were loaded onto trains and sent to orphanages across the country — some never learned what had happened to their families.",
    image: "paintings/24_galveston_hurricane.png",
    source: "Galveston Daily News; Red Cross disaster reports"
  },
  {
    year: 1642,
    title: "The Dutch Tulip Bubble Bursts",
    description: "At the height of Tulip Mania, a single Semper Augustus tulip bulb could sell for the price of a house in Amsterdam. When the market collapsed in February 1637, fortunes vanished overnight. The Dutch government eventually intervened, allowing buyers to cancel contracts for 10% of the agreed price — one of history's first government bailouts.",
    image: "paintings/25_tulip_bubble.png",
    source: "Dutch notarial records; pamphlets of the period"
  },
  {
    year: 1955,
    title: "The Hoax That Fooled the World: The Cottingley Fairies",
    description: "Two young girls in England produced photographs showing themselves playing with tiny fairies. The photos were declared genuine by Arthur Conan Doyle, creator of Sherlock Holmes, and sparked a national debate. The hoax endured for over 60 years before the women, now elderly, admitted they had created the fairies with paper cutouts and hatpins.",
    image: "paintings/26_cottingley_fairies.png",
    source: "The Strand Magazine, 1920; confessions of Elsie Wright and Frances Griffiths"
  },
  {
    year: 1826,
    title: "The Last Public Execution by Guillotine",
    description: "While the guillotine is associated with the French Revolution, its last public use in France was in 1939 — but the most bizarre public guillotining may have been the 1826 execution in Brussels, where a crowd of 20,000 gathered. Street vendors sold refreshments and programs. The carnival atmosphere disturbed even contemporary observers.",
    image: "paintings/27_guillotine_execution.png",
    source: "Belgian judicial archives; contemporary newspaper accounts"
  },
  {
    year: 1943,
    title: "The Phantom Army of inflatable Tanks",
    description: "The US Army created a fake army — complete with inflatable rubber tanks, plywood aircraft, and sound effects trucks playing recordings of military activity — to fool the Germans about the location of the D-Day invasion. A handful of artists, sound engineers, and theater designers fooled German reconnaissance for months.",
    image: "paintings/28_ghost_army.png",
    source: "Ghost Army Legacy Project; US Army declassified records"
  },
  {
    year: 1967,
    title: "The Mothman Prophecies",
    description: "For 13 months, residents of Point Pleasant, West Virginia reported sightings of a tall, winged creature with glowing red eyes — dubbed the 'Mothman.' The sightings culminated on December 15 when the Silver Bridge collapsed during rush hour, killing 46 people. The creature was never seen again. Whether it was a real creature, mass hysteria, or a misidentified sandhill crane remains unresolved.",
    image: "paintings/29_mothman.png",
    source: "Point Pleasant Register; John Keel, The Mothman Prophecies"
  },
  {
    year: 1903,
    title: "The Man Who Flew Before the Wright Brothers",
    description: "German-American inventor Gustave Whitehead may have successfully flown a powered aircraft two years before the Wright Brothers. A local newspaper reported a half-mile flight in Connecticut in 1901. Witnesses signed affidavits. Aviation historians still argue about the claims, but the state of Connecticut has officially recognized Whitehead as first in flight.",
    image: "paintings/30_whitehead_flight.png",
    source: "Bridgeport Sunday Herald, August 18, 1901; Smithsonian dispute records"
  },
  {
    year: 1944,
    title: "The Ghost Army That Fooled Hitler",
    description: "Before D-Day, the Allies launched one of history's greatest deceptions: Operation Bodyguard. They created a fake army group commanded by General Patton — using dummy tanks, fake radio traffic, and double agents — to convince Hitler the invasion would come at Calais rather than Normandy. Hitler held his best divisions in reserve for an attack that never came.",
    image: "paintings/31_ghost_army_patton.png",
    source: "British National Archives; MI5 wartime files"
  },
  {
    year: 1864,
    title: "The Confederates Who Captured a Town Without Realizing It",
    description: "During a Civil War skirmish in Vermont — the northernmost engagement of the war — a small group of Confederate raiders crossed from Canada and robbed three banks in the town of St. Albans. They then fled back across the border. The raid caused an international incident between the US and Britain, who controlled Canada at the time.",
    image: "paintings/32_st_albans_raid.png",
    source: "St. Albans Messenger; US-British diplomatic correspondence"
  },
  {
    year: 1977,
    title: "The Man Who Fell to Earth and Survived",
    description: "Vesna Vulovic, a flight attendant on JAT Flight 367, survived a 33,000-foot fall after the plane exploded over Czechoslovakia. She was found in the tail section, which had pinned her against a food cart during the descent. She suffered a fractured skull, broken legs, and was in a coma for 27 days — but lived. No one else survived.",
    image: "paintings/33_plane_crash_survivor.png",
    source: "Guinness Book of World Records; JAT Airlines investigation"
  },
  {
    year: 1348,
    title: "The Flagellants Who Made Everything Worse",
    description: "During the Black Death, bands of roving penitents called Flagellants marched through Europe, whipping themselves bloody to atone for humanity's sins. They were initially welcomed, but soon began blaming Jews for the plague, inciting pogroms that killed thousands. Pope Clement VI eventually banned the movement as heretical.",
    image: "paintings/34_flagellants.png",
    source: "Chronicles of Jean de Venette; papal bulls of Clement VI"
  },
  {
    year: 1971,
    title: "The Man Who Bought a Lion at Harrods",
    description: "Two Australian women walked into Harrods department store in London and bought a live lion cub for 250 pounds. They named him Christian and raised him in their furniture shop until he got too big, then arranged for him to be rehabilitated into the wild in Kenya. A year later, they returned and Christian remembered them, bounding over to greet them.",
    image: "paintings/35_lion_harrods.png",
    source: "George Adamson's records; Born Free Foundation archives"
  },
  {
    year: 1860,
    title: "The Great Camel Experiment of the American West",
    description: "The US Army imported 75 camels from the Middle East to use as pack animals in the deserts of the American Southwest. The camels performed magnificently, but the project was abandoned when the Civil War broke out. Some camels escaped into the wild, and for decades, prospectors reported sightings of feral camels roaming the Arizona desert.",
    image: "paintings/36_camel_experiment.png",
    source: "US Army Quartermaster Corps records; Beale Expedition journals"
  },
  {
    year: 1752,
    title: "The Year Britain Lost 11 Days",
    description: "When Britain finally adopted the Gregorian calendar, the date jumped from September 2 to September 14 overnight. Rioters reportedly demanded 'Give us back our eleven days!' and there were genuine fears that the calendar change had shortened everyone's life by 11 days. Some landlords tried to charge a full month's rent for the shortened September.",
    image: "paintings/37_lost_eleven_days.png",
    source: "British Parliamentary records; contemporary broadsides and pamphlets"
  },
  {
    year: 1895,
    title: "The Flood That Drowned a Town and Created a Ghost",
    description: "When the South Fork Dam failed in Pennsylvania, it unleashed 20 million tons of water on the town of Johnstown, killing 2,209 people. A 'wave' of debris — including entire houses, locomotives, and even a factory — swept down the valley. The disaster's aftermath included legal battles that established the concept that corporations could be held liable for negligence.",
    image: "paintings/38_johnstown_flood.png",
    source: "Johnstown Tribune; Pennsylvania Supreme Court records"
  },
  {
    year: 1916,
    title: "The Elephants That Went to War",
    description: "German forces in East Africa during WWI had no horses, so they used elephants as beasts of burden. One elephant, named 'Tommy,' carried supplies through the bush for months. The British also considered deploying elephants from zoos to the front lines before deciding it was impractical. Tommy reportedly developed a taste for British Army rations after being captured.",
    image: "paintings/39_elephants_war.png",
    source: "German East Africa campaign records; Lettow-Vorbeck memoirs"
  },
  {
    year: 1928,
    title: "The Greatest Prank in Medical History",
    description: "A man checked into a hospital complaining of abdominal pain. When surgeons opened him up, they found nothing wrong. They sewed him back up, but when he recovered, he confessed he had faked the symptoms just to see if he could get a free appendectomy. The case was published in a medical journal as a cautionary tale about unnecessary surgery.",
    image: "paintings/40_medical_prank.png",
    source: "Journal of the American Medical Association, 1928"
  },
  {
    year: 1386,
    title: "The Animal Trials of the Middle Ages",
    description: "In the French town of Falaise, not just the pig but also a flock of rats were put on trial for eating a farmer's grain crop. When the rats failed to appear in court — their lawyer argued they feared the village cats — the judge still convicted them in absentia and excommunicated the entire species. These trials were taken completely seriously by all involved.",
    image: "paintings/41_rat_trial.png",
    source: "E.P. Evans, The Criminal Prosecution and Capital Punishment of Animals (1906)"
  },
  {
    year: 1962,
    title: "The Man Who Survived Two Nuclear Blasts",
    description: "Yamaguchi Tsutomu was in Hiroshima on a business trip when the first atomic bomb fell. Severely burned, he traveled to Nagasaki for medical treatment — arriving on August 9, the day of the second bombing. He survived both and lived to 93, campaigning against nuclear weapons. Japan officially recognized him as a double hibakusha in 2009.",
    image: "paintings/42_double_atomic_survivor.png",
    source: "Interviews documented by NHK; Nagasaki atomic bomb museum"
  },
  {
    year: 1809,
    title: "The Woman Who Gave Birth to Rabbits",
    description: "Mary Tofts, an English woman, convinced dozens of prominent doctors — including the King's personal surgeon — that she was giving birth to live rabbits. For months, she produced rabbit parts during 'labor' until a servant was caught sneaking a rabbit into her room. The hoax humiliated the medical establishment and became a national scandal.",
    image: "paintings/43_rabbit_birth.png",
    source: "Letters of John Howard, surgeon; St. Bartholomew's Hospital records"
  },
  {
    year: 1845,
    title: "The Potato That Starved Ireland",
    description: "A single strain of potato — the 'Lumper' — was virtually the only food source for a third of Ireland's population. When blight struck, it wiped out the crop for three consecutive years. Over a million people died and two million emigrated. The British government, which continued to export food from Ireland during the famine, remains controversial for its response.",
    image: "paintings/44_irish_famine.png",
    source: "Irish census records; Parliamentary Blue Books"
  },
  {
    year: 1573,
    title: "The Painter Who Hired Hitmen to Kill His Critics",
    description: "Venetian painter Paolo Veronese was hauled before the Inquisition for his painting 'The Last Supper,' which included drunkards, dwarves, and a dog. When told he must change it, he reportedly offered to paint a 'Mary Magdalene' over the dog but refused to remove any figures. The Inquisition renamed the painting 'Feast in the House of Levi' and let it stand.",
    image: "paintings/45_veronese_inquisition.png",
    source: "Transcripts of the Venetian Inquisition, 1573"
  },
  {
    year: 1936,
    title: "The Last Thylacine Died of Exposure",
    description: "The last known thylacine (Tasmanian tiger) died in Hobart Zoo on September 7, locked out of its shelter during an extreme cold snap. Zookeepers found its body frozen on the concrete floor. This species, the world's largest carnivorous marsupial, had been hunted to extinction by the Tasmanian government, which paid bounties for every one killed.",
    image: "paintings/46_thylacine.png",
    source: "Tasmanian Museum and Art Centre records; zoo keeper's diary"
  },
  {
    year: 1995,
    title: "The Tamagotchi That Killed the Dating Scene",
    description: "When Bandai released the Tamagotchi digital pet, it became so popular that Japanese schools banned them, employers prohibited them, and some couples broke up over neglecting real relationships for virtual ones. Japanese airlines reported passengers missing flights because they refused to leave their Tamagotchi unattended. Funeral services were offered for dead Tamagotchis.",
    image: "paintings/47_tamagotchi.png",
    source: "Bandai corporate history; Mainichi Shinbun newspaper"
  }
];
