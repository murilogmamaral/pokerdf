# PokerDF

Converts poker hand history files into structured Pandas DataFrames, making it easier to analyze your games.

Fast and reliable, PokerDF is able to process 3,000 hand history files into _.parquet_ per minute, in a MacBook Air M2 with 8-core CPU.

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

|    | Modality             |   TableSize | BuyIn       |    TournID |   TableID |       HandID | LocalTime           | Level   | Ante   | Blinds      | Owner        | OwnersHand   |   Playing | Player       |   Seat | PostedAnte   | Position    |   PostedBlind |   Stack | PreflopAction        | FlopAction       | TurnAction                 | RiverAction     | AnteAllIn   | PreflopAllIn   | FlopAllIn   | TurnAllIn   | RiverAllIn   | BoardFlop           | BoardTurn              | BoardRiver   | ShowDown    | CardCombination   | Result     |   Balance |   FinalRank | Prize   |
|----|----------------------|-------------|-------------|------------|-----------|--------------|---------------------|---------|--------|-------------|--------------|--------------|-----------|--------------|--------|--------------|-------------|---------------|---------|----------------------|------------------|----------------------------|------------------|-------------|----------------|-------------|-------------|--------------|----------------------|------------------------|--------------|-------------|-------------------|------------|-----------|-------------|---------|
|  0 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | VillainA     |      1 | None         | button      |           nan |     500 | ['folds', '']        | ['', '']         | ['', '']                   | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | folded     |       nan |          -1 | None    |
|  1 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | garciamurilo |      2 | None         | small blind |            10 |     500 | ['calls', '10']      | ['checks', '']    | ['checks', ''], ['folds', ''] | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | folded     |       nan |          -1 | None    |
|  2 | USD Hold'em No Limit |           3 | $1.84+$0.16 | 3026510091 |         1 | 219372022626 | 2020-10-14 10:33:59 | I       | None   | [10.0, 20.0] | garciamurilo | ['6h', 'Ks'] |         3 | VillainB     |      3 | None         | big blind   |            20 |     500 | ['checks', '']       | ['checks', '']    | ['bets', '20']             | ['', '']         | False       | False          | False       | False       | False        | ['4d', 'Qs', 'Qd']   | ['4d', 'Qs', 'Qd', '3s'] | []           | [None, None] | None              | non-sd win |        40 |          -1 | None    |

#### Data Modeling
For advanced analytics, you will need to transform the data and explore different data models. The final structure of your data may vary depending on the specific goals of your project.


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
| ShowDown          | Player's cards if went to showdown                           | [Ah, Ac]                          | list[string]    |
| CardCombination   | Card combination held by the player                          | three of a kind, Aces             | string          |
| Result            | Result of the hand (folded, lost, mucked, non-sd win, won)   | won                               | string          |
| Balance           | Total value won in a hand                                    | 9150.25                           | float           |
| FinalRank         | Player's final ranking in the tournament                     | 1                                 | int             |
| Prize             | Prize won by the player, if any                              | 30000.00                          | float           |

## License
MIT Licence
