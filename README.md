# PokerDF

[![PyPI](https://img.shields.io/pypi/v/pokerdf?color=blue)](https://pypi.org/project/pokerdf/)
[![CI](https://img.shields.io/github/actions/workflow/status/murilogmamaral/pokerdf/ci.yml?branch=main&logo=github&label=CI)](https://github.com/murilogmamaral/pokerdf/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/pokerdf?color=green)](https://github.com/murilogmamaral/pokerdf/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pepy/dt/pokerdf?color=blue)](https://pepy.tech/projects/pokerdf)

Converts poker hand history files into structured Pandas DataFrames, making it easier to analyze your games.

Fast and reliable, PokerDF is able to `convert` 4,000 hand history files, or 85,000 hands, into _.parquet_ per minute, in a MacBook Air M4 with 10-core CPU. The `modeling` command then builds the star schema at 5 million player events per minute.

Currently supports PokerStars. Make sure hand histories are saved in English.

## Introduction

Converting raw hand histories into structured data is the first step toward building a solid poker strategy and maximizing ROI. What are the optimal VPIP, PFR, and C-BET frequencies for No Limit Hold'em 6-Max? In which specific situations is a 3-Bet most profitable? When is bluffing a clear mistake? Once your data is organized in a Pandas DataFrame, the analytical explorations become unlimited, opening new possibilities to fine-tune your decision-making.

In the processed DataFrame, each row corresponds to a specific player in a specific hand, containing all relevant information about that instance of the game. Below, you’ll find an example of hand history before and after processing.

#### Before
```
PokerStars Hand #219372022626: Tournament #3026510091, $1.84+$0.16 USD Hold'em No Limit - Level I (10/20) - 2020/10/14 10:33:59 BRT [2020/10/14 9:33:59 ET]
Table '3026510091 1' 3-max Seat #1 is the button
Seat 1: VillainA (500 in chips) 
Seat 2: garciamurilo (500 in chips) 
Seat 3: VillainB (500 in chips) 
garciamurilo: posts small blind 10
VillainB: posts big blind 20
*** HOLE CARDS ***
Dealt to garciamurilo [6h Ks]
VillainB is disconnected 
VillainA: folds 
garciamurilo: calls 10
VillainB: checks 
*** FLOP *** [4d Qs Qd]
garciamurilo: checks 
VillainB: checks 
*** TURN *** [4d Qs Qd] [3s]
garciamurilo: checks 
VillainB: bets 20
garciamurilo: folds 
Uncalled bet (20) returned to VillainB
VillainB collected 40 from pot
VillainB: doesn't show hand 
*** SUMMARY ***
Total pot 40 | Rake 0 
Board [4d Qs Qd 3s]
Seat 1: VillainA (button) folded before Flop (didn't bet)
Seat 2: garciamurilo (small blind) folded on the Turn
Seat 3: VillainB (big blind) collected (40)
```

#### After

|    | Modality             |   TableSize | BuyIn       |    TournID |   TableID |       HandID | LocalTime           | Level   | Ante   | Blinds      | Owner        | OwnersHand   |   Playing | Player       |   Seat | PostedAnte   | Position    |   PostedBlind |   Stack | Bounty | PreflopAction        | FlopAction       | TurnAction                 | RiverAction     | AnteAllIn   | PreflopAllIn   | FlopAllIn   | TurnAllIn   | RiverAllIn   | BoardFlop           | BoardTurn              | BoardRiver   | ShowDown    | CardCombination   | Result     |   Balance | UncalledReturned | BountyWon | TotalPotLog | Rake | PotBreakdown |   FinalRank | Prize   |
|----|----------------------|-------------|-------------|------------|-----------|--------------|---------------------|---------|--------|-------------|--------------|--------------|-----------|--------------|--------|--------------|-------------|---------------|---------|--------|----------------------|------------------|----------------------------|------------------|-------------|----------------|-------------|-------------|--------------|----------------------|------------------------|--------------|-------------|-------------------|------------|-----------|------------------|-----------|-------------|------|--------------|-------------|---------|
|  0 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | VillainA     |      1 | None         | button      |           nan |     500 | nan    | ['folds', '']        | ['', '']         | ['', '']                   | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | folded     |       nan | nan              | nan       | 40          | 0    | [40.0]       |          -1 | None    |
|  1 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | garciamurilo |      2 | None         | small blind |            10 |     500 | nan    | ['calls', '10']      | ['checks', '']    | ['checks', ''], ['folds', ''] | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | folded     |       nan | nan              | nan       | 40          | 0    | [40.0]       |          -1 | None    |
|  2 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | VillainB     |      3 | None         | big blind   |            20 |     500 | nan    | ['checks', '']       | ['checks', '']    | ['bets', '20']             | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | non-sd win |        40 | 20               | nan       | 40          | 0    | [40.0]       |          -1 | None    |

<br>

## Installation
```
pip install pokerdf
```

## Usage
First, navigate to the directory where you want to save the output:
```
cd output_directory
```
Then, run the package to convert all your hand history files:
```
pokerdf convert /path/to/handhistory/folder
```
After the process completes, you’ll see an output similar to the following:
```
output_directory/
└── output/
   └── 20250510-105423/
      ├── 20200607-T2928873630.parquet
      ├── 20200607-T2928880893.parquet
      ├── 20200607-T2928925240.parquet
      ├── 20200607-T2928950825.parquet
      ├── 20200607-T2928996127.parquet
      ├── 20200607-T2929005994.parquet
      ├── ...
      ├── fail.txt
      └── success.txt
```
#### Details
1. Inside `output` you’ll find a subfolder named with the session ID, in this case, `20250510-105423`, containing all _.parquet_ files.
2. Each hand history file is converted into a _.parquet_ file with the exact same structure, allowing you to concatenate them seamlessly.
3. Each _.parquet_ file follows the naming convention _{DATE_OF_TOURNAMENT}-T{TOURNAMENT_ID}.parquet_.
4. The file `fail.txt` provides detailed information about any files that failed to process. This file is only generated if there are failures.
5. The file `success.txt` lists all successfully converted files. 

#### Incremental pipeline
You may want to build a pipeline to incrementally feed your table with new hand history data. In that case, you can import the `convert_txt_to_tabular_data` function and use it in your workflows. Refer to the docstrings and explore its usage within the package to better understand how it works.

## Metadata
| Column            | Description                                                  | Example                           | Data Type       |
|-------------------|--------------------------------------------------------------|-----------------------------------|-----------------|
| Modality          | The type of game being played                                | Hold'em No Limit                  | string          |
| TableSize         | Maximum number of players                                    | 6                                 | int             |
| BuyIn             | The buy-in amount for the tournament                         | $4.60+$0.40                       | string          |
| TournID           | Unique identifier for the tournament                         | 2928882649                        | string          |
| TableID           | Unique identifier for the table inside a tournament          | 10                                | int             |
| HandID            | Unique identifier for the hand inside a tournament           | 215024616736                      | string          |
| LocalTime         | Local time when the hand was played                          | 2020-06-07 07:44:35               | datetime        |
| Level             | Level of the tournament                                      | IV                                | string          |
| Ante              | Ante amount posted in the hand                               | 10.00                             | float           |
| Blinds            | Big blind and small blind amounts                            | [10.0, 20.0]                      | list[float]     |
| Owner             | Owner of the hand history files                              | ownername                         | string          |
| OwnersHand        | Cards held by the owner in a specific hand                   | [9d, Js]                          | list[string]    |
| Playing           | Number of players active during the hand                     | 5                                 | int             |
| Player            | Player involved in the hand                                  | playername                        | string          |
| Seat              | Seat number of the player                                    | 3                                 | int             |
| PostedAnte        | Amount the player paid for the ante                          | 5.00                              | float           |
| PostedBlind       | Amount the player paid for the blinds                        | 50.00                             | float           |
| Position          | Player's position at the table                               | big blind                         | string          |
| Stack             | Current stack size of the player                             | 2500.00                           | float           |
| Bounty            | Bounty on the player's head, in knockout tournaments         | 0.46                              | float           |
| PreflopAction     | Actions taken during the preflop stage                       | [[checks, ]]                      | list[list[str]] |
| FlopAction        | Actions taken during the flop stage                          | [[bets, 840], [calls, 220]]       | list[list[str]] |
| TurnAction        | Actions taken during the turn stage                          | [[raises, 400], [calls, 500]]     | list[list[str]] |
| RiverAction       | Actions taken during the river stage                         | [[folds, ]]                       | list[list[str]] |
| AnteAllIn         | Whether the player went all-in during the ante               | True                              | bool            |
| PreflopAllIn      | Whether the player went all-in during preflop                | False                             | bool            |
| FlopAllIn         | Whether the player went all-in during the flop               | False                             | bool            |
| TurnAllIn         | Whether the player went all-in during the turn               | False                             | bool            |
| RiverAllIn        | Whether the player went all-in during the river              | False                             | bool            |
| BoardFlop         | Cards dealt on the flop                                      | [4d, Qs, Ad]                      | list[string]    |
| BoardTurn         | Card dealt on the turn                                       | [4d, Qs, Ad, 7d]                  | list[string]    |
| BoardRiver        | Card dealt on the river                                      | [4d, Qs, Ad, 7d, 2d]              | list[string]    |
| ShowDown          | Cards revealed by the player (second is null on single-card shows) | [Ah, Ac]                    | list[string]    |
| CardCombination   | Card combination held by the player                          | three of a kind, Aces             | string          |
| Result            | Result of the hand (folded, lost, mucked, non-sd win, won)   | won                               | string          |
| Balance           | Total value won in a hand                                    | 9150.25                           | float           |
| UncalledReturned  | Uncalled bets returned to the player in the hand             | 600.00                            | float           |
| BountyWon         | Bounty amount won by the player in the hand                  | 0.46                              | float           |
| TotalPotLog       | Total pot of the hand, as reported in the summary            | 840.00                            | float           |
| Rake              | Rake of the hand, as reported in the summary                 | 0.00                              | float           |
| PotBreakdown      | Pots of the hand: main and side pots, or the total pot alone | [5820.0, 3316.0]                  | list[float]     |
| FinalRank         | Final ranking (0 = finished without a reported place, -1 = unknown) | 1                          | int             |
| Prize             | Prize won by the player, if any (satellite tickets: face value) | 30000.00                       | float           |

## Data Modeling
For advanced analytics, you will need to transform the data generated with the package and explore different data models. The final structure of your data may vary depending on the specific goals of your project. You will find below a suggestion of dimensional model (star schema) split into four tables that may be useful for most cases: `fact_player_actions` works as the fact table, holding one row per event of a player in a hand, while `dim_tourn_summary`, `dim_player_summary`, and `dim_final_rank` work as dimension tables.

The reasoning behind this design:

- **The fact is deliberately wide and analysis-ready.** Everything that describes an event — who, where, when, with which stack, facing which board — lives on the row itself, so feature engineering needs no joins. The repetition of hand-level context (level, blinds, table size) is intentional: columnar formats like parquet compress constant-per-hand values to almost nothing, so the storage cost is negligible while every query gets simpler.
- **Posts are events, not metadata.** The ante and blind posts are rows like any action, carrying the real (possibly partial, when all-in) amounts. This makes the pot a pure running sum, gives a row to players that never acted voluntarily (a big blind winning a walk, an all-in on the post), and lets the dynamic `Stack` be reconstructed uniformly.
- **Each dimension answers one question at one grain.** `dim_tourn_summary` describes the tournament (context for slicing); `dim_player_summary` holds the outcome of each player in each hand (result, amount collected, revealed cards); `dim_final_rank` holds the outcome of each player in the tournament. There is no hand dimension on purpose: after moving the hand context into the fact, it would keep a single attribute, and a dimension that thin is better dissolved (`HandID` works as a degenerate dimension, and `LocalTime` lives in the fact).
- **The reconstructed amounts follow the platform's own arithmetic** (bet levels, short all-in blinds, calls above a short post) and were validated against the raw logs: the final `TotalPot` matches the reported "Total pot" in 100% of 135k+ real hands.  


![data-modeling](https://raw.githubusercontent.com/murilogmamaral/pokerdf/main/images/data-modeling.svg)

You can generate these four tables automatically with the `modeling` command, pointing to a folder of _.parquet_ files produced by the `convert` command:
```
pokerdf modeling /path/to/parquet/files
```
The command concatenates all files and saves the four tables as _.parquet_ inside `./modeling/{SESSION_ID}/`.

#### Sharing the data: `--gdpr`

A hand history is not only about you. Under the European General Data Protection Regulation, the nicknames of the other players are personal data — online identifiers of natural persons, in the sense of Article 4(1) and Recital 30 — even though the files came from your own client. The tournament and hand identifiers link every row back to the platform records, and the timestamps allow a hand to be matched against publicly available tournament results. Before sharing a dataset, or moving it outside your own machine, run:
```
pokerdf modeling /path/to/parquet/files --gdpr full
```
Two GDPR principles guide what the command does:

- **Data minimisation (Article 5(1)(c))** — what is not needed to analyze the game is not produced. The dimension tables are not generated at all, since they exist to describe who the players are: the nickname of the owner of the logs, the buy-in paid, the cards revealed at showdown, the final rank and the prizes received. `LocalTime` is removed from the fact table.
- **Pseudonymisation (Article 4(5))** — `TournID`, `HandID` and `Player` are replaced by salted BLAKE2b digests. The same nickname always maps to the same pseudonym, so grouping and joining keep working, but nothing points back to a person or to a hand that can be looked up on the platform.

Everything that makes the data worth analyzing is preserved: the order of the actions, the amounts, the pot, the stacks, the board and the positions.

Two modes are available:

| Mode | What it does |
|------|--------------|
| `--gdpr full` | Anonymizes everyone, including you: your hole cards (`OwnerC1`, `OwnerC2`) are also removed, since they are repeated on every row of a hand and mark which player is the owner of the logs. |
| `--gdpr keep-owner` | Protects the other players exactly the same way, but keeps your nickname and your hole cards. The GDPR restricts what you share about *others*, not about yourself: this is the mode for sharing your game with a coach or a study group. |

By default the salt is random and never stored. Recital 26 draws the line between anonymous and personal data at whether re-identification is reasonably likely — and without the salt, a nickname cannot be confirmed by hashing a guess, so the pseudonyms are irreversible. To append new sessions to an existing dataset, the pseudonyms must be stable across runs, so inform your own salt:
```
pokerdf modeling /path/to/parquet/files --gdpr full --salt your-secret
```
With a kept salt the result remains *pseudonymized* personal data in the sense of the GDPR, not anonymous data: protect the salt as carefully as the original files, since whoever holds it can confirm a nickname by hashing it.

Each session writes an `anonymization.txt` report next to the data, describing what was applied and which risks remain — the most relevant being that the owner plays in every hand of their own archive, so even in `full` mode the pseudonym present in all rows is the owner; and that a hand remains described by its board and its exact bet sequence, which is close to unique for anyone holding another copy of it. None of this replaces assessing, for your own case, whether sharing the data is lawful.

#### fact_player_actions

One row per event of a player: the ante and blind posts open each hand as rows (with the real — possibly partial — amounts that left each stack), followed by every action, sorted exactly as the hand unfolded: rounds in chronological order, starting from the first seat to act (the seat after the big blind on preflop, the seat after the button postflop). The amounts are reconstructed by replaying each round with the betting rules of the game, so they reflect the chips that actually moved.

| Column      | Description                                                                                           | Example     |
|-------------|-------------------------------------------------------------------------------------------------------|-------------|
| TournID     | Tournament in which the action happened                                                               | 2928882649  |
| HandID      | Hand in which the action happened                                                                     | 215024616736|
| LocalTime   | Time when the hand was played                                                                         | 2020-06-07 07:52:12 |
| TableSize   | Maximum number of players at the table                                                                | 9           |
| Playing     | Number of players active in the hand                                                                  | 6           |
| Level       | Level of the tournament, as an integer                                                                | 15          |
| Ante        | Ante of the hand                                                                                      | 4.0         |
| SmallBlind  | Nominal small blind of the hand                                                                       | 15.0        |
| BigBlind    | Nominal big blind of the hand                                                                         | 30.0        |
| Round       | Round of the action (preflop, flop, turn, river)                                                      | preflop     |
| Player      | Player who acted                                                                                      | playername  |
| Seat        | Seat number of the player                                                                             | 4           |
| Position    | Position of the player (button, small blind, big blind), when any                                     | big blind   |
| Stack       | Stack of the player right after the event (starting stack minus everything pushed so far)             | 2340.0      |
| PostedAnte  | Ante posted by the player in the hand (partial when all-in)                                           | 4.0         |
| PostedBlind | Blind posted by the player in the hand (partial when all-in)                                          | 30.0        |
| Action      | The event (posts ante, posts small/big blind, folds, checks, calls, bets, raises)                     | raises      |
| ActionIndex | Order of the action among the player's actions in the round (0 for posts)                             | 1           |
| ActionOrder | Chronological sequence of the action inside the hand (1..n)                                           | 3           |
| AddedValue  | Exact chips pushed by the action                                                                      | 50.0        |
| TotalValue  | Total put in by the player in the round after the action (on preflop includes the posted ante/blind)  | 64.0        |
| TotalPot    | Total pot right after the action (uncalled bets returned at the end are not discounted)               | 156.0       |
| BoardC1..C5 | Board visible at the moment of the action (empty on preflop, 3 cards on flop, 4 on turn, 5 on river)  | 4d, Tc, 7s  |
| OwnerC1..C2 | Hole cards of the owner of the logs                                                                   | Ah, Qd      |

#### dim_tourn_summary

One row per tournament.

| Column         | Description                          | Example              |
|----------------|--------------------------------------|----------------------|
| TournID        | Unique identifier of the tournament  | 2928882649           |
| LocalStartTime | Time of the first hand               | 2020-06-07 07:44:35  |
| Modality       | The type of game being played        | USD Hold'em No Limit |
| BuyIn          | The buy-in of the tournament         | $4.60+$0.40          |
| Owner          | Owner of the hand history files      | ownername            |

#### dim_player_summary

One row per player in each hand, holding the outcome: the result, the amount collected and the cards revealed at showdown (also for the losers, useful for range studies — null when the player did not reveal them).

| Column         | Description                                                | Example    |
|----------------|-------------------------------------------------------------|------------|
| TournID        | Tournament of the hand                                     | 2928882649 |
| HandID         | Hand in which the player participated                      | 215024616736 |
| Player         | Name of the player                                         | playername |
| Result         | Result of the hand (folded, lost, mucked, non-sd win, won) | won        |
| Balance        | Amount collected from the pot by the player in the hand (null when nothing was collected; the winners' amounts sum to the pot) | 840.0      |
| ShowDownC1..C2 | Cards revealed by the player at showdown                   | Ah, Ac     |
| PokerHand      | Card combination shown by the player                       | a pair of Aces |

#### dim_final_rank

One row per player in each tournament.

| Column    | Description                                                             | Example    |
|-----------|--------------------------------------------------------------------------|------------|
| TournID   | Tournament played                                                       | 2928882649 |
| Player    | Name of the player                                                      | playername |
| FinalRank | Final rank in the tournament (0 when finished without a reported place, -1 when not registered in the logs) | 27         |
| Prize     | Prize received, when any                                                | 0.24       |

## License
MIT Licence
