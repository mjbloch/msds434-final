from flask import Flask, render_template, request
from google.cloud import bigquery
import pandas as pd
import sys


app = Flask(__name__, template_folder='./templates')

# For local testing
# credentials = "msds434-final-394319-6e3e1682d8d3.json"
# client = bigquery.Client.from_service_account_json(credentials, project='msds434-final-394319')

# for Cloud Run deployment
client = bigquery.Client(project='msds434-final-394319')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        data = request.form
        age = int(data['age'])
        gender = data['gender']
        tenure = int(data['tenure'])
        usage = int(data['usage'])
        support_calls = int(data['support_calls'])
        pmt_delay = int(data['pmt_delay'])
        sub_type = data['sub_type']
        contract_length = data['contract_length']
        total_spend = int(data['total_spend'])
        last_interaction = int(data['last_interaction'])

        prediction_input = [{
            "Age": age,
            "Gender": gender,
            "Tenure": tenure,
            "Usage_Frequency": usage,
            "Support_Calls": support_calls,
            "Payment_Delay": pmt_delay,
            "Subscription_Type": sub_type,
            "Contract_Length": contract_length,
            "Total_Spend": total_spend,
            "Last_Interaction": last_interaction
        }]

        ingestion_df = pd.DataFrame(
            prediction_input,
            columns = [
                "Age",
                "Gender",
                "Tenure",
                "Usage_Frequency",
                "Support_Calls",
                "Payment_Delay",
                "Subscription_Type",
                "Contract_Length",
                "Total_Spend",
                "Last_Interaction"
            ]
        )

        job_config = bigquery.LoadJobConfig(
            schema = [
                bigquery.SchemaField("Age", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Gender", bigquery.enums.SqlTypeNames.STRING),
                bigquery.SchemaField("Tenure", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Usage_Frequency", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Support_Calls", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Payment_Delay", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Subscription_Type", bigquery.enums.SqlTypeNames.STRING),
                bigquery.SchemaField("Contract_Length", bigquery.enums.SqlTypeNames.STRING),
                bigquery.SchemaField("Total_Spend", bigquery.enums.SqlTypeNames.INTEGER),
                bigquery.SchemaField("Last_Interaction", bigquery.enums.SqlTypeNames.INTEGER),
            ],
            write_disposition="WRITE_TRUNCATE",
        )

        ingest = client.load_table_from_dataframe(
            ingestion_df, 'msds434-final-394319.churn.churn_input', job_config=job_config
        )

        ingest.result()
        
        query = """
                SELECT * FROM 
                ML.predict( MODEL churn.churn_prediction, 
                            (SELECT * FROM `msds434-final-394319.churn.churn_input`)
                )
                """
        
        prediction_result_df = client.query(query).to_dataframe()
        
        temp = prediction_result_df.iloc[0][1]
        prob = dict(temp[1])['prob']
        

        prediction_result_df['churn_probability'] = [prob]

        prediction_result_df = prediction_result_df.drop('predicted_Churn_probs', axis=1)
        
        prediction_result_df = prediction_result_df[[
                'predicted_Churn', 
                'churn_probability', 
                'Age', 
                'Gender', 
                'Tenure', 
                'Usage_Frequency', 
                'Support_Calls', 
                'Subscription_Type',
                'Contract_Length',
                'Total_Spend',
                'Last_Interaction'
        ]]
        
        html_table = prediction_result_df.to_html()

        return render_template('results.html', html_table=html_table)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)