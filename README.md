# Gulf infrastructure under fire, Feb–Oct 2026

What the 2026 strikes and the closure of the Strait of Hormuz cost Gulf energy producers and governments, and what they did to shipping. An independent student research project by Jackson Mackney, built from public sources only.

**Read the report:** [`report/Mackney_Gulf_War_Costs_2026-11-10.pdf`](report/Mackney_Gulf_War_Costs_2026-11-10.pdf) (12 pages)

## Main findings

All figures are base cases. Page 11 of the report shows what each one is built from and what would move it.

| Finding | Figure | Basis |
|---|---|---|
| Oil and gas output lost across six Gulf states, January to September, valued at 2025 prices | about $96bn | Estimated; trade data for four states agree within 5% |
| Gained from higher prices on what was still produced | about $86bn | Estimated; trade data suggest about a quarter less |
| Net for Qatar, Kuwait and Bahrain, which have no route around the strait | about –$48bn | Estimated |
| Saudi Arabia's net gain against a year earlier | +$16bn on our method; about +$5bn in Saudi customs data | Estimated, checked against customs data |
| Strike damage at 53 fixed sites (repairs plus lost output) | $16.6bn, range $5.5bn to $51bn | Modelled |
| Interceptors fired by Gulf states | $9.0bn, range $3bn to $35bn | Modelled |
| Ships seen by trackers in Hormuz since 8 March, against 2025 | –94% | Measured (ships broadcasting position) |
| Struck sites hit again within two weeks | about 1 in 5 | Measured (44 locations) |

Three things to know before quoting any of this:

1. The export figures are my calculation, not reported revenue. They use output estimates and benchmark prices, and they compare with the same months of 2025. I checked them against official trade statistics: the lost volume holds up (about $84bn against my $87bn for the four states that publish figures), but my price gain runs high, so Saudi Arabia came out only slightly ahead of 2025.
2. The strike-damage figure rests mostly on assumptions. No owner of a large site has published a repair bill, and one site (Ras Laffan) is more than half the total.
3. The ship count misses vessels that sail with trackers off. By October most crude was moving again even though the count stayed near its low.

## What is in this repository

| Folder | Contents |
|---|---|
| `report/` | The report as a PDF |
| `data/` | The tables behind the export, strike-damage and shipping pages |
| `code/` | The Python that draws those charts, and the script that pulls ship-traffic data |
| `figures/` | The charts as images |

### Data files

- `export_losses_tidy.csv`: one row per state, product and period: output in 2026 and 2025, prices, the value of output lost, the price gain, and the source and reliability of each row.
- `export_losses_by_state.csv`: totals by state and by product, with a check that the rows add up to the headline.
- `strait_traffic_daily.csv`: daily ship counts at the Strait of Hormuz, Bab el-Mandeb, the Suez Canal and the Cape of Good Hope, 1 January 2025 to 8 November 2026, by ship type (IMF PortWatch).
- `strait_traffic_summary.json`: the headline traffic numbers and the windows they cover.
- `strike_damage_by_site.csv`: base, low and high damage estimates for each priced site.
- `strike_damage_by_weapon.json`: the same total split by weapon.
- `trade_check_by_state.csv`: our figures for each state beside the change in export value shown by official trade statistics (Saudi, Qatari, Kuwaiti and Omani figures, and what Japan, Korea, India, the EU, the UK and Singapore report importing).
- `pub_figs_numbers.json`: every number drawn on the new charts, with its source.

### Rebuilding the charts

```
pip install pandas numpy matplotlib
cd code
python3 pub_figs.py                # redraws the charts into ../figures
python3 refresh_strait_traffic.py  # optional: pulls the latest ship counts from IMF PortWatch
```

## What is not here

- The strike log (466 checked reports, graded A to C) and the cost model workbooks. These are working files; ask if you want to see them.
- The charts on repeat strikes, the defence bill, satellite flares and the outlook are built from those working files, so their code is not included.

## Sources

US Energy Information Administration (Short-Term Energy Outlook), International Energy Agency, OPEC, IMF PortWatch, NASA FIRMS, World Bank, company filings (Saudi Aramco, DP World and others), the Baltic Exchange, broker quotes reported by trade press, and government statements. Each page of the report lists its own sources.

## Dates

Strike log to 28 October 2026. Export losses to 30 September 2026. Market and shipping data to 10 November 2026.

## How it was made

AI tools did the volume: collecting, sorting and checking sources. I set the questions and made the calls. Every page was checked against its data by a second pass before release.

## Contact

Jackson Mackney · University of Chicago · [LinkedIn](https://www.linkedin.com/in/jackson-mackney-5a1195257)
