from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager, get_all_data)
import pandas as pd
import altair as alt
from kgcontroller import select_all_soknader

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'  # nødvendig for session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/barnehager')
def barnehager():
    information = select_alle_barnehager()
    return render_template('barnehager.html', data=information)

@app.route('/behandle', methods=['GET', 'POST'])
def behandle():
    if request.method == 'POST':
        sd = request.form
        print(sd)

        # Sjekk om nødvendige felter er fylt ut
        required_fields = [
            'navn_forelder_1', 'navn_forelder_2', 'adresse_forelder_1', 'adresse_forelder_2',
            'tlf_nr_forelder_1', 'tlf_nr_forelder_2', 'personnummer_forelder_1', 'personnummer_forelder_2',
            'personnummer_barnet_1', 'liste_over_barnehager_prioritert_5', 'tidspunkt_for_oppstart', 'brutto_inntekt_husholdning'
        ]
        
        for field in required_fields:
            if not sd.get(field):
                return render_template('soknad.html', error="Alle feltene må fylles ut.", data=sd)

        # Her henter vi barnehagene og deres tilgjengelige plasser
        ledige_plasser = [
            {'barnehage_id': 1, 'barnehage_navn': 'Sunshine Preschool', 'ledige_plasser': 15},
            {'barnehage_id': 2, 'barnehage_navn': 'Happy Days Nursery', 'ledige_plasser': 2},
            {'barnehage_id': 3, 'barnehage_navn': '123 Learning Center', 'ledige_plasser': 4},
            {'barnehage_id': 4, 'barnehage_navn': 'ABC Kindergarten', 'ledige_plasser': 0},
            {'barnehage_id': 5, 'barnehage_navn': 'Tiny Tots Academy', 'ledige_plasser': 5},
            {'barnehage_id': 6, 'barnehage_navn': 'Giggles and Grins Childcare', 'ledige_plasser': 0},
            {'barnehage_id': 7, 'barnehage_navn': 'Playful Pals Daycare', 'ledige_plasser': 6}
        ]
        
        # Sjekk om valgt barnehage har ledige plasser
        valgt_barnehage = sd.get('liste_over_barnehager_prioritert_5')
        for barnehage in ledige_plasser:
            if barnehage['barnehage_navn'] == valgt_barnehage:
                if barnehage['ledige_plasser'] > 0:
                    # Sjekk inntekt (det kan være et kriterium for prioritering)
                    brutto_inntekt = int(sd.get('brutto_inntekt_husholdning'))
                    if brutto_inntekt >= 500000:  # Eksempel på inntektskrav
                        status = "Tilbud: Barnehageplass er tilgjengelig!"
                    else:
                        status = "Avslag: Inntekten er for lav for tilbud."
                else:
                    # Hvis barnehagen er full, sjekk fortrinnsrett
                    fortrinnsrett_barnevern = sd.get('fortrinnsrett_barnevern')
                    fortrinnsrett_sykdom_i_familien = sd.get('fortrinnsrett_sykdom_i_familien')
                    fortrinnsrett_sykdome_paa_barnet = sd.get('fortrinnsrett_sykdome_paa_barnet')
                    
                    if fortrinnsrett_barnevern or fortrinnsrett_sykdom_i_familien or fortrinnsrett_sykdome_paa_barnet:
                        status = "Tilbud: Barnehageplass tildeles pga. fortrinnsrett."
                    else:
                        status = "Avslag: Ingen ledige plasser i valgt barnehage."
                break
        else:
            status = "Avslag: Barnehagen finnes ikke i systemet."
        
        # Lagre data og vis resultat
        session['information'] = sd
        
        # Lagre søknaden i databasen
        soknad = form_to_object_soknad(sd)
        insert_soknad(soknad)
        commit_all()  # Lagre alle data til Excel-filen
        
        return render_template('svar.html', status=status)
    else:
        return render_template('soknad.html')    
    
    # -------- Oppdatert svar --------
@app.route('/svar')
def svar():
    information = session['information']
    
    # Hent informasjon om barnehager og sjekk for plasser
    barnehager = select_alle_barnehager()

    # Inspeksjon for å finne riktig attributtnavn:
    for barnehage in barnehager:
        print(barnehage.__dict__)  # Skriv ut attributtene til barnehagene for å finne den riktige ID-en
    
    # Her antar vi at 'barnehage_id' er den riktige attributtnavnet
    barnehage_id = information.get('barnehage_id')  # Hent barnehage_id fra søknadsdataene

    # Legg til en sjekk om barnehage_id er None eller ugyldig
    if barnehage_id is None:
        return render_template('svar.html', data=information, svar="Ingen barnehage valgt.")

    # Forsikre oss om at barnehage_id er et gyldig tall
    try:
        barnehage_id = int(barnehage_id)
    except ValueError:
        return render_template('svar.html', data=information, svar="Ugyldig barnehage ID.")

    # Finn den relevante barnehagen
    barnehage = next((b for b in barnehager if b.barnehage_id == barnehage_id), None)

    if not barnehage:
        return render_template('svar.html', data=information, svar="Barnehagen finnes ikke.")

    # Sjekk om det er ledige plasser eller fortrinnsrett
    if barnehage.ledige_plasser > 0:
        # Anta at vi får fortrinnsrett som en del av informasjonen
        fortrinnsrett = information.get('fortrinnsrett', False)  # Kan være True eller False

        if fortrinnsrett or barnehage.ledige_plasser > 0:
            barnehage.ledige_plasser -= 1  # En plass tildeles
            svar = "TILBUD"
        else:
            svar = "AVSLAG"
    else:
        svar = "AVSLAG"

    return render_template('svar.html', data=information, svar=svar)


    # --------------- Ny soknader ---------
@app.route('/soknader')
def soknader():
    all_soknader = select_all_soknader()  # Henter alle søknader fra databasen
    print("All søknader:", all_soknader)  # Debugging

    ledige_plasser = select_alle_barnehager()  # Henter informasjon om ledige plasser i barnehager
    print("Ledige plasser:", ledige_plasser)  # Debugging

    for soknad in all_soknader:
        valgt_barnehage = soknad.get('barnehager_prioritert')
        print("Valgt barnehage:", valgt_barnehage)  # Debugging

        if valgt_barnehage is None:
            soknad['status'] = "AVSLAG: Mangler prioritert barnehage."
            continue

        barnehage_funnet = False
        for barnehage in ledige_plasser:
            print("Sjekker barnehage:", barnehage.barnehage_navn)  # Debugging
            if barnehage.barnehage_navn == valgt_barnehage:
                barnehage_funnet = True
                print("Barnehage funnet:", barnehage.barnehage_navn)  # Debugging
                if barnehage.barnehage_ledige_plasser > 0:
                    brutto_inntekt = soknad.get('brutto_inntekt')
                    print("Brutto inntekt:", brutto_inntekt)  # Debugging
                    if brutto_inntekt is None:
                        soknad['status'] = "AVSLAG: Mangler brutto inntekt."
                        continue

                    brutto_inntekt = int(brutto_inntekt)
                    if brutto_inntekt >= 500000:
                        soknad['status'] = "TILBUD"
                    else:
                        soknad['status'] = "AVSLAG: Inntekten er for lav for tilbud."
                else:
                    fortrinnsrett = soknad.get('fr_barnevern') or soknad.get('fr_sykd_familie') or soknad.get('fr_sykd_barn')
                    print("Fortrinnsrett:", fortrinnsrett)  # Debugging
                    if fortrinnsrett and fortrinnsrett != 'nan' and fortrinnsrett != '':
                        soknad['status'] = "TILBUD: Fortrinnsrett"
                    else:
                        soknad['status'] = "AVSLAG: Ingen ledige plasser"
                break

        if not barnehage_funnet:
            soknad['status'] = "AVSLAG: Barnehagen finnes ikke i systemet."

    print("Søknader med status:", all_soknader)  # Debugging
    return render_template('soknader.html', soknader=all_soknader)

    # --------------------- Oppdatert commit

@app.route('/commit')
def commit():
    try:
        all_data = get_all_data()  # Henter data fra databasen
        if not isinstance(all_data, dict):
            raise ValueError("Data should be a dictionary")
        return render_template('commit.html', data=all_data)
    except Exception as e:
        return f"An error occurred: {e}", 500

# ------------- Legge inn Oblig 3 statistikken ----------------

@app.route('/statistikk')
def statistikk():
    # Hente dataen fra Excel
    kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", 
                           sheet_name="KOSandel120000", 
                           header=3, 
                           names=['kom', 'y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'], 
                           na_values=['.', '..'])

    # Rense data. Fjerne NAN.
    kgdata_clean = kgdata.dropna()

    # Legge til gjennomsnittlig prosent på en trygg måte
    kgdata_clean = kgdata_clean.assign(Gjennomsnitt=kgdata_clean[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1))

    # Diagram for prosent fra 2015 til 2023 for en valgt kommune (her bruker vi "0301 Oslo" som eksempel)
    kommune_data = kgdata_clean[kgdata_clean['kom'] == '0301 Oslo'].copy()
    kommune_data = kommune_data.melt(id_vars=['kom'], var_name='År', value_name='Prosent')
    kommune_data['År'] = kommune_data['År'].str.extract(r'(\d+)').astype(float) + 2000

    chart_g = alt.Chart(kommune_data).mark_line(point=True).encode(
        x=alt.X('År:O', title='År'),
        y=alt.Y('Prosent:Q', title='Prosent barn i barnehage'),
        tooltip=['År', 'Prosent']
    ).properties(
        title='Prosent barn i ett- og toårsalderen i barnehage (2015-2023) - Oslo'
    )

    # Konverter diagrammet til HTML
    chart_g_html = chart_g.to_html()

    return render_template('statistikk.html', chart_g_html=chart_g_html)

"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""