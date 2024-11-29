from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)

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
        return render_template('svar.html', status=status)
    else:
        return render_template('soknad.html')

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

@app.route('/commit')
def commit():
    commit_all()
    return render_template('commit.html')

"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

