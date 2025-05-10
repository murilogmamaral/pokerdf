# PokerDF

Converts poker hand history files into structured Pandas DataFrames, making it easier to analyze your games.

Fast and reliable, PokerDF is able to process 3,000 hand history files into _.parquet_ per minute, in a MacBook Air M2 with 8-core CPU.

Currently supports PokerStars. Make sure hand histories are saved in English.

## Introduction

Converting raw hand histories into structured data is the first step toward building a solid poker strategy and maximizing ROI. What are the optimal VPIP, PFR, and C-BET frequencies for No Limit Hold'em 6-Max? In which specific situations is a 3-Bet most profitable? When is bluffing a clear mistake? Once your data is organized in a Pandas DataFrame, the analytical explorations become unlimited, opening new possibilities to fine-tune your decision-making.

## Installation
```
pip install pokerdf
```

## Usage
Navigate to the folder where you want to save the output:
```
cd output_directory
```
Then, run the package like this:
```
pokerdf convert /path/to/handhistory/folder
```

Once the process is concluded, you will find something like this:
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

## DataFrame structure
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
