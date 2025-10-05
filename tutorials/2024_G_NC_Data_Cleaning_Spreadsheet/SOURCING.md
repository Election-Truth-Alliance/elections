## Data Sourcing

One of the most common questions we get asked is "Where do you get your election data?" It's all public data and available on the state
or county's website. That's where we get it and you can also find it.

Unfortunately, there is very little consistency across states and counties on how they provide election data. Sometimes
you can go to the state website and they sufficiently detailed data from all counties, all precincts and all voter
methods. Other times, you have go to the individual county in the state and see how they present it. If you are lucky,
you find an Excel or CSV file. Other times, you're manually entering data you found from a blurry photocopied of a dot
matrix printout from a hard to navigate county website. For this tutorial, we'll be using North Carolina as an example. They have great state level election
data, granted, in a text file but one that is easy to import into a spreadsheet. The good part about going to the state
level is you get all the data in one place. The bad part is that the files are usually pretty large and hard to work with
and don't always provide as much detail.

You need two types of data:
- Vote tallies with the following data:
  - Precinct level vote data
  - The type of vote (mail-in, in-person, etc.)
  - The number of votes given to each candidate
  - The total number of votes cast for that precinct
- Registration data
  - For each precinct, how many registered voters were capable of voting in that election. This helps determine turnout data.

Sometimes vote tallies come with registration data, but often they are two different data sources.

In the case of North Carolina, the data is available on the official 
[North Carolina State Board of Elections](https://www.ncsbe.gov/results-data/voter-turnout/2024-general-election-turnout)
website.

The source of the vote tallies is [here](https://www.ncsbe.gov/results-data/election-results/historical-election-results-data)
and the actual file [here](https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/results_pct_20241105.zip).

Registration data is [here](https://www.ncsbe.gov/results-data/voter-registration-data) and the actual 
file [here](https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/voter_stats_20241105.zip).

There is also layout files included on the page for each data source. It is often the case that the data ends up being a database
dump, often contains codes and abbreviations and sometimes, even foreign keys, these files are good ways
to decode that data. The data sources and the layout files are available in the [/data/US_NC/original/2024](../../data/US_NC/2024)
directory of this repo.

> Note: websites can change and this link may move at some point.

The downloaded files:

- [results_pct_20241105.zip](../../data/US_NC/2024/results_pct_20241105.zip) - The voting data by precinct<br/>
- [layout_results_pct.txt](../../data/US_NC/2024/voter_stats_20241105.zip) - Voting data layout
- [layout_ncvoter.txt](../../data/US_NC/2024/layout_ncvoter.txt) - Registration data layout
- [voter_stats_20241105.zip](../../data/US_NC/2024/voter_stats_20241105.zip) - Registration data

### Next: [Cleaning](CLEANING.md)