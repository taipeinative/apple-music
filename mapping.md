# Mapping Apple Music data

This is an demo of integrating Apple Music data to the iTunes libraries.

## Load Tagged Libraries

I've manually tagged the meta data of songs in Microsoft Excel, including the vocal type, the language, and the additional tags of the tracks. Let's load the all time **top 1000 listened** tracks from my iTunes library:

```python
from iTunes import Utils
import pandas as pd

MAP = r'.\data\tmm.yaml'
TAG = r'.\data\lib-tagged.xlsx'

top_tagged_df = Utils.clean_tagged_excel(TAG)
display(top_tagged_df.head(10))
```

|    | Name                              | Artist                             |   Year |   Play Count | Total Time             | Vocal   | Language   | Genre        | Tags                                              |
|---:|:----------------------------------|:-----------------------------------|-------:|-------------:|:-----------------------|:--------|:-----------|:-------------|:--------------------------------------------------|
|  0 | Forest of Clock                   | ARForest                           |   2020 |          492 | 0 days 00:02:29.603000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)          |
|  1 | Next Life                         | SadBois, Sam Varga, Natalia Taylar |   2024 |          418 | 0 days 00:02:40        | V.M     | English    | Dance        | ('Bass.FutureBass', 'Rock.Influenced', nan)       |
|  2 | Nothing                           | PIKASONIC                          |   2022 |          388 | 0 days 00:03:37.200000 | A       | -          | Dance        | ('Bass.FutureBass', 'Bass.KawaiiBass', nan)       |
|  3 | 箱庭デイブレイク (feat. nayuta)   | Shurin, Sound-Box, nayuta          |   2021 |          368 | 0 days 00:03:11.100000 | V.F     | Japanese   | Pop          | ('Soundtrack.VideoGame.Deemo', nan, nan)          |
|  4 | Try (feat. RØRY) [Fairlane Remix] | MitiS, RØRY, Fairlane              |   2021 |          334 | 0 days 00:03:15.113000 | V.F     | English    | Dance        | ('Bass.FutureBass', nan, nan)                     |
|  5 | Orbit (feat. Jazemarie)           | RUQOA, Jazemarie                   |   2020 |          328 | 0 days 00:04:08.653000 | V.F     | English    | Dance        | ('Dubstep.MelodicDubstep', nan, nan)              |
|  6 | Enough (feat. Hatsune Miku)       | Mwk, Hatsune Miku                  |   2022 |          322 | 0 days 00:03:28.696000 | V.F     | Japanese   | Dance        | ('Dubstep.MelodicDubstep', nan, nan)              |
|  7 | Through Mist and Fog              | iolli                              |   2022 |          307 | 0 days 00:02:52.773000 | V.F     | English    | Dance        | ('Soundtrack.VideoGame.Deemo', nan, nan)          |
|  8 | Hyouryu (piano ver.)              | SLSMusic                           |   2022 |          304 | 0 days 00:03:03.040000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)          |
|  9 | Start It Over (feat. KC)          | Last Heroes, Man Cub, KC           |   2022 |          296 | 0 days 00:03:15.600000 | V.F     | English    | Dance        | ('Dubstep.MelodicDubstep', 'Pop.Influenced', nan) |

(If you're wondering, the meaning of symbols in Vocal column: *A* for acoustic, *V.F* for female vocalist, *V.M* for male vocalist, and *V.X* for female and male vocalists.)

## Append Apple Music ID

To integrate Apple Music data to the tracks, we need the Apple Music ID for the tracks so the further data collection can resume. Since iTunes didn't export the id of the tracks, and I couldn't afford the Apple Developer program either, here I used [Tune My Music](https://www.tunemymusic.com/) to read my temporary public-shared playlist which contains all songs from my library, and then downloaded them as a CSV. [The file](https://github.com/taipeinative/apple-music/blob/master/data/tmm.csv) contains the Apple ID and ISRC of the tracks, but some tracks still missed the match. Again, I provided a [manual match map](https://github.com/taipeinative/apple-music/blob/master/data/tmm.yaml) so eventually 96% of tracks can be linked to Apple Music.

```python
TMM = r'.\data\tmm.csv'
tmm = pd.read_csv(TMM) # The match result from Tune My Music
display(tmm.head(10))
```

|    | Track name                               | Artist name                 | Album                                         | Playlist name   | Type     | ISRC         |   Apple - id |
|---:|:-----------------------------------------|:----------------------------|:----------------------------------------------|:----------------|:---------|:-------------|-------------:|
|  0 | Can't Pretend                            | Nyman                       | Can't Pretend - Single                        | All             | Playlist | QZHN32450270 |   1734422144 |
|  1 | Before We Say Goodbye (feat. Trella)     | GhostDragon                 | Before We Say Goodbye (feat. Trella) - Single | All             | Playlist | USA2P2421340 |   1741639059 |
|  2 | Searching... (Cyberworld Pt. II)         | MOKKAI                      | Searching... (Cyberworld Pt. II) - Single     | All             | Playlist | QZK6H2419717 |   1744175878 |
|  3 | Springtime                               | Aika                        | Springtime - Single                           | All             | Playlist | QZHNB2498608 |   1739445281 |
|  4 | ギターと孤独と蒼い惑星                   | kessoku band                | 結束バンド                                    | All             | Playlist | JPE302201022 |   1657318765 |
|  5 | Daisies                                  | Linney                      | Daisies - Single                              | All             | Playlist | QZUCN2201574 |   1735970692 |
|  6 | Lie Awake                                | SadBois, Xyan & Donna Tella | Lie Awake - Single                            | All             | Playlist | QZSYP2444652 |   1740842824 |
|  7 | Galaxy Trip                              | DarTokki                    | Cotton Candy Vol. 2 - EP                      | All             | Playlist | QM42K2015686 |   1506251882 |
|  8 | Moments (Club Edit) [feat. クサカアキラ] | Mameyudoufu                 | encore plus chapitre 01 (feat. クサカアキラ)  | All             | Playlist | TCJPL2080018 |   1516972217 |
|  9 | Dhalia                                   | Ujico                       | Flowers                                       | All             | Playlist | USCGJ1808787 |   1727121488 |

```python
COLS = ['Name', 'Artist', 'Year', 'Play Count', 'Total Time', 'Vocal', 'Language', 'Genre', 'Tags', 'ISRC', 'Apple ID']

top_matched, top_unmatched = Utils.match_tmm_data(path = TMM, df = top_tagged_df, escape_artists = ['接個吻,開一槍'])
top_matched2, top_unmatched2 = Utils.apply_map(top_unmatched, MAP, TMM)
print(f'Before manual maps | Matched: {len(top_matched)}, Unmatched: {len(top_unmatched)}')
print(f'After manual maps  | Matched: {len(top_matched) + len(top_matched2)}, Unmatched: {len(top_unmatched2)}\nThe unmatched tracks:')
display(top_unmatched2[COLS].head(10))
```

Before manual maps | Matched: 564, Unmatched: 436<br/>
After manual maps  | Matched: 960, Unmatched: 40<br/>
The unmatched tracks:

|     | Name                              | Artist               |   Year |   Play Count | Total Time             | Vocal   | Language   | Genre        | Tags                                                                          |   ISRC |   Apple ID |
|----:|:----------------------------------|:---------------------|-------:|-------------:|:-----------------------|:--------|:-----------|:-------------|:------------------------------------------------------------------------------|-------:|-----------:|
|   7 | Through Mist and Fog              | iolli                |   2022 |          307 | 0 days 00:02:52.773000 | V.F     | English    | Dance        | ('Soundtrack.VideoGame.Deemo', nan, nan)                                      |    nan |        nan |
|  16 | Antheia                           | ARForest             |   2022 |          270 | 0 days 00:02:06.302000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', 'Dance.Influenced', nan)                       |    nan |        nan |
|  41 | Hyperbola                         | SIHanatsuka          |   2020 |          213 | 0 days 00:04:00.143000 | A       | -          | Dance        | ('Dubstep.MelodicDubstep', 'Soundtrack.VideoGame.Cytus', nan)                 |    nan |        nan |
|  42 | for you                           | Sawano Hiroyuki      |   2006 |          212 | 0 days 00:02:33.469000 | A       | -          | Instrumental | ('Soundtrack.Anime', nan, nan)                                                |    nan |        nan |
|  82 | アスは雨が止むから (feat. Ato)    | HyuN, Ato            |   2018 |          164 | 0 days 00:02:33.808000 | V.F     | Japanese   | Rock         | ('Dance.Influenced', nan, nan)                                                |    nan |        nan |
|  86 | Dream together                    | Hydra Tsai (INSPION) |   2022 |          161 | 0 days 00:02:41.776000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)                                      |    nan |        nan |
| 105 | 光                                | 姜米条               |   2019 |          152 | 0 days 00:02:11.866000 | A       | -          | Dance        | ('Hard.Hardcore', 'Soundtrack.VideoGame.Phigros', nan)                        |    nan |        nan |
| 109 | Igallta                           | Se-U-Ra              |   2020 |          151 | 0 days 00:02:02.148000 | A       | -          | Dance        | ('Hard.JCore', 'Soundtrack.VideoGame.Phigros', 'Soundtrack.VideoGame.Lanota') |    nan |        nan |
| 125 | Red Storm Sentiment (feat. kalon) | Tsukasa, kalon       |   2018 |          140 | 0 days 00:03:20.751000 | V.F     | Japanese   | Pop          | ('Soundtrack.VideoGame.Deemo', 'Soundtrack.VideoGame.Cytus', nan)             |    nan |        nan |
| 130 | THE BEGINNING                     | Cytus                |   2021 |          138 | 0 days 00:02:18.187000 | A       | -          | Dance        | ('Dubstep.MelodicDubstep', nan, nan)                                          |    nan |        nan |

```python
merged = pd.concat([top_matched, top_matched2.drop(columns = ['Matched']), top_unmatched2.drop(columns = ['Matched'])]).sort_index()
display(merged.head(10))
```

|    | Name                              | Artist                             |   Year |   Play Count | Total Time             | Vocal   | Language   | Genre        | Tags                                              | ISRC         |      Apple ID |
|---:|:----------------------------------|:-----------------------------------|-------:|-------------:|:-----------------------|:--------|:-----------|:-------------|:--------------------------------------------------|:-------------|--------------:|
|  0 | Forest of Clock                   | ARForest                           |   2020 |          492 | 0 days 00:02:29.603000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)          | TCAIY2489252 |   1846247318 |
|  1 | Next Life                         | SadBois, Sam Varga, Natalia Taylar |   2024 |          418 | 0 days 00:02:40        | V.M     | English    | Dance        | ('Bass.FutureBass', 'Rock.Influenced', nan)       | GBRKQ2471487 |   1735859643 |
|  2 | Nothing                           | PIKASONIC                          |   2022 |          388 | 0 days 00:03:37.200000 | A       | -          | Dance        | ('Bass.FutureBass', 'Bass.KawaiiBass', nan)       | AUBEC2172934 |   1612209081 |
|  3 | 箱庭デイブレイク (feat. nayuta)   | Shurin, Sound-Box, nayuta          |   2021 |          368 | 0 days 00:03:11.100000 | V.F     | Japanese   | Pop          | ('Soundtrack.VideoGame.Deemo', nan, nan)          | TCJPN2160657 |   1547980403 |
|  4 | Try (feat. RØRY) [Fairlane Remix] | MitiS, RØRY, Fairlane              |   2021 |          334 | 0 days 00:03:15.113000 | V.F     | English    | Dance        | ('Bass.FutureBass', nan, nan)                     | GBEWA2104693 |   1806737034 |
|  5 | Orbit (feat. Jazemarie)           | RUQOA, Jazemarie                   |   2020 |          328 | 0 days 00:04:08.653000 | V.F     | English    | Dance        | ('Dubstep.MelodicDubstep', nan, nan)              | QM42K2091333 |   1511595991  |
|  6 | Enough (feat. Hatsune Miku)       | Mwk, Hatsune Miku                  |   2022 |          322 | 0 days 00:03:28.696000 | V.F     | Japanese   | Dance        | ('Dubstep.MelodicDubstep', nan, nan)              | JP92Q2200305 |   1647319659 |
|  7 | Through Mist and Fog              | iolli                              |   2022 |          307 | 0 days 00:02:52.773000 | V.F     | English    | Dance        | ('Soundtrack.VideoGame.Deemo', nan, nan)          | nan          | nan           |
|  8 | Hyouryu (piano ver.)              | SLSMusic                           |   2022 |          304 | 0 days 00:03:03.040000 | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)          | QZPJ32177419 |   1694564691 |
|  9 | Start It Over (feat. KC)          | Last Heroes, Man Cub, KC           |   2022 |          296 | 0 days 00:03:15.600000 | V.F     | English    | Dance        | ('Dubstep.MelodicDubstep', 'Pop.Influenced', nan) | GBEWA2202190 |   1806726066 |

---

<div style="display: flex; justify-content: space-between;">
  <div style="text-align: left;">
    ◂ <a href="./merging.md">Merging library</a>
  </div>
</div>
