# Merging iTunes Libraries

This is a demo of merging two iTunes libraries. This is useful, particularly when comparing an old library with the new one.

```python
from iTunes import Library, Utils
```

## Load Libraries

Here presents an example where two libraries are merged. `lib1`'s source is a Microsoft Excel file from April 2025, and `lib2`'s source is an iTunes XML file from November 2025.

```python
lib1 = Library.from_excel(r'..\..\xlsx\Library-2025-04.xlsx', sheet = 0)
display(lib1.data.head())
```

|    |   Track ID | Name                              | Artist                             |   Composer | Album                    | Genre         |   Year | Date Modified   | Date Added   |   Play Count |   Size | Total Time   |   Disc Number |   Track Number | Vocal   | Language   | Sub Genres   | Sub Tags                                    |
|---:|-----------:|:----------------------------------|:-----------------------------------|-----------:|:-------------------------|:--------------|-------:|:----------------|:-------------|-------------:|-------:|:-------------|--------------:|---------------:|:--------|:-----------|:-------------|:--------------------------------------------|
|  0 |        nan | Forest of Clock                   | ARForest                           |        nan | Forest of Clock - Single | Soundtrack    |   2020 | NaT             | NaT          |          487 |    nan | NaT          |           nan |            nan | A       | -          | Instrumental | ('Soundtrack.VideoGame.Deemo', nan, nan)    |
|  1 |        nan | Next Life                         | SadBois, Sam Varga, Natalia Taylar |        nan | Next Life - Single       | English Dance |   2024 | NaT             | NaT          |          395 |    nan | NaT          |           nan |            nan | V.M     | English    | Dance        | ('Bass.FutureBass', 'Rock.Influenced', nan) |
|  2 |        nan | Nothing                           | PIKASONIC                          |        nan | Nothing - Single         | Future Bass   |   2022 | NaT             | NaT          |          368 |    nan | NaT          |           nan |            nan | A       | -          | Dance        | ('Bass.FutureBass', 'Bass.KawaiiBass', nan) |
|  3 |        nan | 箱庭デイブレイク (feat. nayuta)   | しゅーりん, Sound-Box, nayuta      |        nan | After Garden             | Soundtrack    |   2021 | NaT             | NaT          |          367 |    nan | NaT          |           nan |            nan | V.F     | Japanese   | Pop          | ('Soundtrack.VideoGame.Deemo', nan, nan)    |
|  4 |        nan | Try (feat. RØRY) [Fairlane Remix] | MitiS, RØRY, Fairlane              |        nan | Lost (Deluxe)            | English Dance |   2021 | NaT             | NaT          |          326 |    nan | NaT          |           nan |            nan | V.F     | English    | Dance        | ('Bass.FutureBass', nan, nan)               |

```python
lib2 = Library.from_msgpack(r'.\data\lib-cln.msgpack')
display(lib2.data.head())
```

|    |   Track ID | Name       | Artist     |   Composer | Album                        | Genre     |   Year | Date Modified       | Date Added          |   Play Count |     Size | Total Time             |   Disc Number |   Track Number | Tags          |
|---:|-----------:|:-----------|:-----------|-----------:|:-----------------------------|:----------|-------:|:--------------------|:--------------------|-------------:|---------:|:-----------------------|--------------:|---------------:|:--------------|
|  0 |       3816 | 十年       | ['陳奕迅'] |        nan | THE 1ST ELEVEN YEARS 然後呢? | Mando Pop |   2008 | 2020-12-20 01:08:28 | 2020-12-02 14:24:31 |           40 |  8144121 | 0 days 00:03:21.926000 |             1 |                | {'Mandarin'}  |
|  1 |       3818 | 也可以     | ['閻奕格'] |        nan | 我有我自己                   | Mando Pop |   2017 | 2021-02-15 14:59:40 | 2021-02-16 05:48:44 |           22 |  4418942 | 0 days 00:04:30.680000 |             1 |             10 | {'Mandarin'}  |
|  2 |       3820 | 大哥       | ['衛蘭']   |        nan | My Love                      | Canto Pop |   2005 | 2021-03-29 11:03:21 | 2020-12-02 14:24:31 |           26 |  4335914 | 0 days 00:03:50.739000 |               |                | {'Cantonese'} |
|  3 |       3822 | 小手拉大手 | ['梁靜茹'] |        nan | 親親                         | Mando Pop |   2006 | 2021-03-29 10:56:28 | 2020-12-02 13:50:11 |           17 |  4658111 | 0 days 00:04:04.349000 |               |                | {'Mandarin'}  |
|  4 |       3824 | 小幸運     | ['田馥甄'] |        nan | 小幸運                       | Mando Pop |   2015 | 2021-03-29 10:59:10 | 2020-12-02 14:24:31 |           23 | 10709820 | 0 days 00:04:25.586000 |               |                | {'Mandarin'}  |

## Merge Libraries

To merge two libraries, the module compares the artists and the name of the track to determine whether two tracks match. The result includes the merged (matched) library, and the entries only present on either sides. It is normal that some tracks can't be matched; the titles, the artist sets, and even the artists' name sometimes change. In the provided example, the numbers of unmatched tracks are 227 tracks and 413 tracks in `lib1` and `lib2`.

```python
merger = Library.merge(lib1, lib2)
print(merger)

display(merger.matched.head())

print('Only in lib1')
display(merger.prev_only.head())

print('Only in lib2')
display(merger.next_only.head())
```

iTunes Library Merge Result \<Matched/Left Only/Right Only: 2111/227/413>

|    |   Track ID | Name                        | Artist                     | Composer     | Album              | Genre       |   Year | Date Modified       | Date Added          |   Play Count |        Size | Total Time             |   Disc Number |   Track Number | Vocal   | Language   | Sub Genres   | Sub Tags                       | Tags                                      |
|---:|-----------:|:----------------------------|:---------------------------|:-------------|:-------------------|:------------|-------:|:--------------------|:--------------------|-------------:|------------:|:-----------------------|--------------:|---------------:|:--------|:-----------|:-------------|:-------------------------------|:------------------------------------------|
|  0 |       7396 | "My Last Day"               | ['YOURNESS']               | Syohei Koga  | 6 Case             | J Rock      |   2021 | 2023-04-07 10:44:13 | 2023-05-15 01:06:42 |           49 | 1.02519e+07 | 0 days 00:04:55.882000 |             1 |             12 | nan     | nan        | nan          | (nan, nan, nan)                | {'Rock', 'Japanese'}                      |
|  1 |       8632 | #03                         | ['STEREO DIVE FOUNDATION'] | R・O・N      | STEREO DIVE 03     | Anime       |   2024 | 2024-12-12 15:47:27 | 2025-11-06 04:52:23 |           10 | 8.05237e+06 | 0 days 00:03:40.125000 |             1 |              1 | nan     | nan        | nan          | (nan, nan, nan)                | {'Temporary'}                             |
|  2 |       5650 | #imissyousobad (feat. Yalu) | ['原子邦妮', 'Yalu']       | nan          | 謝謝你曾經讓我悲傷 | Mando Dance |   2017 | 2021-08-03 08:11:03 | 2021-08-03 08:11:03 |           90 | 8.08968e+06 | 0 days 00:03:45.948000 |             1 |              4 | V.F     | Mandarin   | Pop          | ('Dance.Influenced', nan, nan) | {'Mandarin', 'Dance/Electronic', 'Fresh'} |
|  3 |       8826 | 01                          | ['Kamisaki Nei']           | Kamisaki Nei | 01 - Single        | Anime       |   2025 | 2025-03-13 13:20:14 | 2025-11-06 04:52:23 |           17 | 1.02382e+07 | 0 days 00:04:32        |             1 |              1 | nan     | nan        | nan          | (nan, nan, nan)                | {'Temporary'}                             |
|  4 |       5092 | 1,2,3 (feat. HATIK)         | ['Amel Bent', 'HATIK']     | nan          | 1,2,3 - Single     | French Pop  |   2020 | 2021-01-03 05:02:27 | 2021-01-03 06:01:23 |           76 | 3.79839e+06 | 0 days 00:03:43.111000 |             1 |                | V.X     | French     | Pop          | (nan, nan, nan)                | {'French'}                                |

Only in lib1

|     |   Track ID | Name                                                       | Artist                                                                        |   Composer | Album                                                                   | Genre       |   Year | Date Modified   | Date Added   |   Play Count |   Size | Total Time   |   Disc Number |   Track Number | Vocal   | Language   | Sub Genres   | Sub Tags                      |
|----:|-----------:|:-----------------------------------------------------------|:------------------------------------------------------------------------------|-----------:|:------------------------------------------------------------------------|:------------|-------:|:----------------|:-------------|-------------:|-------:|:-------------|--------------:|---------------:|:--------|:-----------|:-------------|:------------------------------|
|   7 |        nan | 10℃                                                        | ['しゃろう']                                                                  |        nan | 10℃ - Single                                                            | Future Bass |   2021 | NaT             | NaT          |           68 |    nan | NaT          |           nan |            nan | A       | -          | Dance        | ('Bass.FutureBass', nan, nan) |
|   9 |        nan | 115万キロのフィルム                                        | ['Official HIGE DANdism']                                                     |        nan | エスカパレード                                                          | J Rock      |   2018 | NaT             | NaT          |           25 |    nan | NaT          |           nan |            nan | nan     | nan        | nan          | (nan, nan, nan)               |
|  23 |        nan | 25コ目の染色体                                             | ['RADWIMPS']                                                                  |        nan | RADWIMPS 3 ~無人島に持っていき忘れた一枚~                               | J Rock      |   2005 | NaT             | NaT          |           32 |    nan | NaT          |           nan |            nan | nan     | nan        | nan          | (nan, nan, nan)               |
| 228 |        nan | Blue Light (feat. Hatsune Miku, 鏡音リン, Gackpoid & ANRI) | ['Amamori P', 'Hatsune Miku', 'Kagamine Rin', 'Gackpoid', 'ANRI', '鏡音リン'] |        nan | Picaresque (feat. Hatsune Miku, Kagamine Rin, Megpoid, ANRI & Gackpoid) | Pop         |   2024 | NaT             | NaT          |           19 |    nan | NaT          |           nan |            nan | nan     | nan        | nan          | (nan, nan, nan)               |
| 250 |        nan | Brand-New                                                  | ['SANARI']                                                                    |        nan | Sicksteen                                                               | J Rock      |   2019 | NaT             | NaT          |           65 |    nan | NaT          |           nan |            nan | V.M     | Japanese   | Rock         | ('Pop.Influenced', nan, nan)  |

Only in lib2

|    | Name                                                    |   Track ID | Artist                                  | Composer         | Album                                                            | Genre       |   Year | Date Modified       | Date Added          |   Play Count |     Size | Total Time             |   Disc Number |   Track Number | Tags                           |
|---:|:--------------------------------------------------------|-----------:|:----------------------------------------|:-----------------|:-----------------------------------------------------------------|:------------|-------:|:--------------------|:--------------------|-------------:|---------:|:-----------------------|--------------:|---------------:|:-------------------------------|
|  0 | 10C                                                     |       7188 | ['しゃろう']                            | しゃろう         | 10c - Single                                                     | Future Bass |   2021 | 2023-01-12 14:04:40 | 2023-01-27 03:14:29 |           69 |  8012430 | 0 days 00:03:37.500000 |             1 |              1 | {'(Bass)', 'Dance/Electronic'} |
|  1 | 115 Million Kilometer Film                              |       5730 | ['Official HIGE DANdism']               | Satoshi Fujihara | Escaparade                                                       | J Rock      |   2018 | 2021-08-17 00:38:03 | 2021-08-17 00:38:03 |           26 | 11465290 | 0 days 00:05:24.633000 |             1 |              1 | {'Rock', 'Japanese'}           |
|  2 | 25kome No Senshokutai                                   |       5798 | ['RADWIMPS']                            | Yojiro Noda      | RADWIMPS 3 - Mujintou Ni Motteikiwasureta Ichimai                | J Rock      |   2005 | 2021-08-17 00:54:13 | 2021-08-17 00:54:13 |           34 | 11195263 | 0 days 00:05:16.640000 |             1 |              5 | {'Rock', 'Japanese'}           |
|  3 | A Flower of the Ground                                  |       8612 | ['Seventeen Years Old and Berlin Wall'] | Yusei Tsuruta    | Reflect - EP                                                     | Alternative |   2017 | 2024-11-25 15:38:20 | 2025-11-06 04:52:23 |          115 | 10008213 | 0 days 00:04:29        |             1 |              1 | {'Temporary'}                  |
|  4 | A truth seeker -Communication with Utopia will be lost- |       9100 | ['KURO']                                | KURO             | A truth seeker -Communication with Utopia will be lost- - Single | Electronic  |   2024 | 2025-08-05 08:22:03 | 2025-11-06 04:52:23 |            4 |  4678208 | 0 days 00:02:00.583000 |             1 |              1 | {'Temporary'}                  |

## Merge Libraries with Conditional Maps

Since the module couldn't find the matches for over 400 tracks, one can provide the [conditional conversion maps for track titles](https://github.com/taipeinative/apple-music/blob/master/data/names.yaml) and [simple conversion maps for artists](https://github.com/taipeinative/apple-music/blob/master/data/artists.yaml). With these maps, the number of unmatched tracks decrease to 2 and 188 tracks in `lib1` & `lib2`, where the former are due to deletion and the latter are due to addition.

```python
artists: dict[str, str            | list[str]]                        = Utils.read_yaml(r'.\data\artists.yaml')
names:   dict[str, dict[str, str] | list[dict[str, str | list[str]]]] = Utils.read_yaml(r'.\data\names.yaml')
merger = Library.merge(lib1, lib2, artists, ['接個吻,開一槍'], names)
print(merger)

print('Only in lib1')
display(merger.prev_only.head())

print('Only in lib2')
display(merger.next_only.head())
```

iTunes Library Merge Result \<Matched/Left Only/Right Only: 2336/2/188\>

Only in lib1

|    | Name                                                    |   Track ID | Artist       | Composer   | Album                                                            | Genre      |   Year | Date Modified       | Date Added          |   Play Count |    Size | Total Time             |   Disc Number |   Track Number | Tags          |
|---:|:--------------------------------------------------------|-----------:|:-------------|:-----------|:-----------------------------------------------------------------|:-----------|-------:|:--------------------|:--------------------|-------------:|--------:|:-----------------------|--------------:|---------------:|:--------------|
|  0 | A truth seeker -Communication with Utopia will be lost- |       9100 | ['KURO']     | KURO       | A truth seeker -Communication with Utopia will be lost- - Single | Electronic |   2024 | 2025-08-05 08:22:03 | 2025-11-06 04:52:23 |            4 | 4678208 | 0 days 00:02:00.583000 |             1 |              1 | {'Temporary'} |
|  1 | About U                                                 |       9180 | ['ROY KNOX'] | Roy Levi   | About U - Single                                                 | Dubstep    |   2023 | 2025-09-08 06:14:49 | 2025-11-06 04:52:23 |            6 | 7366367 | 0 days 00:03:18.400000 |             1 |              1 | {'Temporary'} |
|  2 | Afraid To Love                                          |       9174 | ['ROY KNOX'] | nan        | Ophelia Presents: Advent Volume 5                                | Dance      |   2022 | 2025-09-08 06:13:47 | 2025-11-06 04:52:23 |            6 | 8308287 | 0 days 00:03:56.800000 |             1 |              3 | {'Temporary'} |
|  3 | Alone                                                   |       9046 | ['SHUNTA']   | SHUNTA     | Decorate                                                         | Electronic |   2025 | 2025-07-02 23:29:49 | 2025-11-06 04:52:23 |           15 | 6273845 | 0 days 00:02:37.168000 |             1 |              5 | {'Temporary'} |
|  4 | Am I Wrong?                                             |       9006 | ['capo2']    | capo2      | Love Letter - EP                                                 | Pop        |   2025 | 2025-06-02 16:24:51 | 2025-11-06 04:52:23 |           59 | 6846759 | 0 days 00:03:04.333000 |             1 |              3 | {'Temporary'} |

Only in lib2

|      |   Track ID | Name           | Artist             |   Composer | Album            | Genre    |   Year | Date Modified   | Date Added   |   Play Count |   Size | Total Time   |   Disc Number |   Track Number | Vocal   | Language   | Sub Genres   | Sub Tags                  |
|-----:|-----------:|:---------------|:-------------------|-----------:|:-----------------|:---------|-------:|:----------------|:-------------|-------------:|-------:|:-------------|--------------:|---------------:|:--------|:-----------|:-------------|:--------------------------|
|  690 |        nan | Happier        | ['Tanner Patrick'] |        nan | Happier - Single | Pop/Rock |   2018 | NaT             | NaT          |           60 |    nan | NaT          |           nan |            nan | V.M     | English    | Pop          | (nan, nan, nan)           |
| 1603 |        nan | Sweet Nothings | ['DOM.J']          |        nan | Free Space - EP  | Rock     |   2020 | NaT             | NaT          |           65 |    nan | NaT          |           nan |            nan | A       | -          | Rock         | ('Alternative', nan, nan) |

## Finish Merging

After merging, the merger object can turn back into a library object. The latest track from `lib2` will be automatically added to the new library, but this can be configured as well.

```python
lib3 = merger.as_lib(include_next = True)
print(lib3)
```

iTunes Library <2524 tracks>

---

<div style="display: flex; justify-content: space-between;">
  <div style="text-align: left;">
    ◂ <a href="./cleaning.md">Cleaning library</a>
  </div>
  <div style="text-align: right;">
    <a href="./mapping.md">Mapping Apple Music data</a> ▸
  </div>
</div>
