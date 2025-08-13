from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import json
from tqdm import tqdm
import os

#Configure 4-bit quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,  
    bnb_4bit_quant_type="nf4",            
    bnb_4bit_use_double_quant=True,       
)

#Load tokenizer and 4-bit quantized Qwen3-14B
model_name = "Qwen/Qwen3-14B"  
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto",  

)



def analyze_sentiment(current_comment):
    analysis_prompt = f"""
        Analyze the electric vehicle charging station review. 
        First determine the overall sentiment (Negative=6, Positive=7, Neutral=8) based on the review.
        Then, provide the most relevant category (1-5 or other=9) and 1-3 key words
        **Critical Rules**  
    
        category:
        1. **Charging Functionality & Reliability** - ONLY basic functionality: Assess comments about hardware operation, faults, offline status, damage, and reliability. Keywords include but are not limited to working, works, operational, functional, broken, dead, offline, problems, issues, error, fault, neveikia, disabled, maintenance, fixed, repair, power, units. 
        2. **Charging Performance** - Evaluate mentions of technical metrics: charging speed, power output (kW/kWh/Amps/Volts).Keywords include but are not limited to kw, kwh, amps, volts, rate, max, slow, quick, fast, charging fast, charging speed fast, 11kw, 45kw, miles, mph, top, peak.
        3. **Location & Availability** - Judge feedback about geographical placement, discoverability, parking space availability, and obstruction issues (e.g., ICEing).Keywords include but are not limited to location, parking, spots, blocked, spaces, occupied, find, locate, access, stalls, open, convenient, easy, difficult, bay, empty, full, busy, parking, occupied.
        4. **Pricing & Payment** - Analyze comments regarding costs, additional fees, and payment process/methods (apps, cards, etc.).Keywords include but are not limited to price, cost, expensive, cents, rate, fee, gratis, free, vend, kostenlos, charges, parking fee, too expensive, app, account, card, network, pay, activate, service.
        5. **Environment & Service** - Evaluate surroundings (cleanliness, noise), amenities, staff service, and user comfort.Keywords include but are not limited to good, great, nice, excellent, experience, convenient, easy, simple, clean, helpful, service, friendly, quiet, amenities, environment, love, place, super, fantastic, perfect, awesome, review, satisfied. 
        9. **Other** - Review does not belong to any of the above categories.
        - Charging Functionality & Reliability ONLY covers basic function. Examples:  
        - "Charges very fast" → [category] = Charging Performance  
        - "Charger is broken" → [category] = Charging Functionality & Reliability

        Key words Extraction:
        - Key words MUST be extracted from the review AND TRANSLATED TO ENGLISH. Do not include non-English words in the final output.

        Sentiment Labels:
        - Negative (6): Explicit complaints (e.g., "环境差，充电慢" → 6,5,bad environment, slow charging).
        - Positive (7): Explicit praise (e.g., "Worked great. It was our first time to charge our new Bolt. It was easy and intuitive."→ 7,1,Worked great,easy).
        - Neutral (8): Objective facts (no sentiment)(e.g.,"Charging power: 50kW." → 8,2,power)
    
        Answer strictly according to [Overall_Sentiment],[category],[keyword].
        Now analyze: {current_comment}
    """
    messages = [
                    {"role": "user", "content": analysis_prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=10)
    
 
    response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response.strip()

def processing(review_file,output_file):
    #Load dataset   
    with open(review_file, 'r', encoding='utf-8') as input_file:

        dataset = {'comment_list':json.load(input_file)['comment_list'][:300]}
    
        try:
            progress_bar = tqdm(dataset['comment_list'], desc="Processing comments")
            mmm = 0
            for comment_data in progress_bar:
                current_comment = comment_data["content"]
                mmm+=1

                sentiment = analyze_sentiment(current_comment)
                print(current_comment)
                print(sentiment)
                comment_data['sentiment'] = sentiment
            

                if mmm % 1000 == 0:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=4)
    
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=4)

def main():
    #china
    review_file = os.path.join("Data","input","china_comments.json")
    output_file = os.path.join("Data","interim","LLM_result","china_comments.json")
    processing(review_file,output_file)
    
    #usa
    review_file = os.path.join("Data","input","usa_comments.json")
    output_file = os.path.join("Data","interim","LLM_result","usa_comments.json")
    processing(review_file,output_file)
    
    #europe
    review_file = os.path.join("Data","input","europe_comments.json")
    output_file = os.path.join("Data","interim","LLM_result","europe_comments.json")
    processing(review_file,output_file)

if __name__ == "__main__":
    main()
