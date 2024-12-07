import pandas as pd  # Hente riktig bibliotek
import altair as alt  # Hente Altair bibliotek for visualiserings delen av oppgaven

# Hente dataen fra Excel
# Legge Excel i samme mappe som denne filen
kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", 
                       sheet_name="KOSandel120000", 
                       header=3, 
                       names=['kom', 'y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'], 
                       na_values=['.', '..'])

# Skrive ut de første radene av datasettet for å sjekke at det er lastet inn riktig
print(kgdata.head())

# Rense data. Fjerne NAN.
kgdata_clean = kgdata.dropna()  # Dropna fjerner NAN (Not a number)
print("Rensede data:")
print(kgdata_clean.head())

# Legge til gjennomsnittlig prosent på en trygg måte
kgdata_clean = kgdata_clean.assign(Gjennomsnitt=kgdata_clean[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1))

# Høyest i 2023
highest_2023 = kgdata_clean.loc[kgdata_clean['y23'].idxmax()]

# Lavest i 2023
lowest_2023 = kgdata_clean.loc[kgdata_clean['y23'].idxmin()]

print("\nHøyest prosent i 2023:")
print(highest_2023)
print("\nLavest prosent i 2023:")
print(lowest_2023)

# Høyest og lavest gjennomsnitt fra 2015 til 2023
highest_avg = kgdata_clean.loc[kgdata_clean['Gjennomsnitt'].idxmax()]
lowest_avg = kgdata_clean.loc[kgdata_clean['Gjennomsnitt'].idxmin()]

print("\nHøyest gjennomsnitt fra 2015 til 2023:")
print(highest_avg)

print("\nLavest gjennomsnitt fra 2015 til 2023:")
print(lowest_avg)

# Gjennomsnittlig prosent for 2020
average_2020 = kgdata_clean['y20'].mean()
print(f"\nGjennomsnittlig prosent for 2020: {average_2020}")

# Diagram for prosent fra 2015 til 2023 for en valgt kommune (her bruker vi "0301 Oslo" som eksempel)
kommune_data = kgdata_clean[kgdata_clean['kom'] == '0301 Oslo'].copy() # copy brukes for å kopiere datasettet og ikke endre dataen
kommune_data = kommune_data.melt(id_vars=['kom'], var_name='År', value_name='Prosent')
# melt endrer datasettet fra bredt til langt format
# id_vars er kolonnen som skal identifiseres. var value/name gir navn til nye kolonner
# Resultatet er at hver rad nå representerer ett år og prosentandelen av barn i barnehagen for det året.
kommune_data['År'] = kommune_data['År'].str.extract(r'(\d+)').astype(float) + 2000  # Legger til 2000 for riktig årstall
# str.extract for å hente ut årstallet fra kolonnen 'År'. RegEx-mønsteret (\d+) fanger alle siffer (det vil si årstallet)
chart_g = alt.Chart(kommune_data).mark_line(point=True).encode( # alt.chart lager diagram i altair # mark_line velger linjediagram
    x=alt.X('År:O', title='År'), # encode med dette videre spesifiserer hvordan dataen skal vises
    y=alt.Y('Prosent:Q', title='Prosent barn i barnehage'),
    tooltip=['År', 'Prosent']
).properties( # properties gir egenskaper. her overskrift.
    title='Prosent barn i ett- og toårsalderen i barnehage (2015-2023) - Oslo'
)

# Diagram for de 10 kommunene med høyest gjennomsnittlig prosent fra 2015 til 2023
top_10_kommuner = kgdata_clean.nlargest(10, 'Gjennomsnitt') # finner de 10 største basert på kolonnen gjennomsnitt
top_10_data = top_10_kommuner.melt(id_vars=['kom'], var_name='År', value_name='Prosent') #melt og idvars som tidligere. gjør år og prosent til variabler
top_10_data['År'] = top_10_data['År'].str.extract(r'(\d+)').astype(float) + 2000  # Legger til 2000 for riktig årstall

chart_h = alt.Chart(top_10_data).mark_line(point=True).encode( # opretter nytt alt diagram
    x=alt.X('År:O', title='År'),
    y=alt.Y('Prosent:Q', title='Prosent barn i barnehage'),
    color=alt.Color('kom:N', title='Kommune'), # velger at farger viser ulike kommuner
    tooltip=['kom', 'År', 'Prosent'] # viser informasjon hvis du holder over en kommune med musa
).properties(
    title='Gjennomsnittlig prosent barn i barnehage (2015-2023) - Topp 10 kommuner'
)

# Vis diagrammene
chart_g.display()
chart_h.display()
# Virket ikke å vise, så prøver å lagre grafene som HTML så jeg kan åpne de på en annen måte.
# Usikker om Thonny har mulighet for visualisering.
chart_g.save('chart_g.html')
chart_h.save('chart_h.html')