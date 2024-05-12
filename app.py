import streamlit as st
import anthropic, re

with open('prompts/metaprompt.txt', 'r') as file:
    metaprompt = file.read().replace('\n', '')

MODEL_NAME = "claude-3-opus-20240229"

def extract_between_tags(tag: str, string: str, strip: bool = False) -> list[str]:
    ext_list = re.findall(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL)
    if strip:
        ext_list = [e.strip() for e in ext_list]
    return ext_list

def remove_empty_tags(text):
    return re.sub(r'\n<(\w+)>\s*</\1>\n', '', text, flags=re.DOTALL)

def strip_last_sentence(text):
    sentences = text.split('. ')
    if sentences[-1].startswith("Let me know"):
        sentences = sentences[:-1]
        result = '. '.join(sentences)
        if result and not result.endswith('.'):
            result += '.'
        return result
    else:
        return text

def extract_prompt(metaprompt_response):
    between_tags = extract_between_tags("Instructions", metaprompt_response)[0]
    return between_tags[:1000] + strip_last_sentence(remove_empty_tags(remove_empty_tags(between_tags[1000:]).strip()).strip())

def extract_variables(prompt):
    pattern = r'{([^}]+)}'
    variables = re.findall(pattern, prompt)
    return set(variables)

def pretty_print(message):
    return '\n\n'.join('\n'.join(line.strip() for line in re.findall(r'.{1,100}(?:\s+|$)', paragraph.strip('\n'))) for paragraph in re.split(r'\n\n+', message))
# pretty_print(message)

# Function to call the model API with input text and API key
def call_model(input_text, api_key):
    
    CLIENT =  anthropic.Anthropic(api_key=api_key)
    variable_string = ""
    # for variable in input_variables:
    #     variable_string += "\n{$" + variable.upper() + "}"

    prompt = metaprompt.replace("{{TASK}}", input_text)
    assistant_partial = "<Inputs>"
    if variable_string:
        assistant_partial += variable_string + "\n</Inputs>\n<Instructions Structure>"

    message = CLIENT.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content":  prompt
            },
            {
                "role": "assistant",
                "content": assistant_partial
            }
        ],
        temperature=0
    ).content[0].text

    extracted_prompt_template = extract_prompt(message)
    variables = extract_variables(message)

    output_text = pretty_print(extracted_prompt_template)
    # st.write("Variables:" + str(variables))
    # st.write("\n************************\n")
    st.text_area("", output_text, height=400)
    return output_text
    

# Streamlit interface
def main():
    generated = False
    output_text = ""
    button_text = "Genereer"

    # st.title("Prompt-Generator Demo")
    # st.write("Enter your Task to generate prompt.")

    input_task = st.text_input("Wat wil je jouw chatbot laten doen?")
    # input_var = st.text_input("Input Variables")

    st.markdown(
    """
    <style>
        div [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
)


    if st.button(button_text, use_container_width=True):
        #gif_runner = st.markdown("<img src='./gifs/spinner.gif' width='100' style='display: block; margin: 0 auto;'>" , unsafe_allow_html=True)
        gif_runner = st.image("./gifs/spinner.gif", width=200)
        output_text = call_model(input_task, st.secrets["anthropic_api_key"])
        gif_runner.empty()
        generated = True
        button_text = "Genereer opnieuw"
        

    if generated:
        st.download_button('Download Prompt', output_text, 'prompt.txt')
        st.write("\n\n***********************************************\n\n")


if __name__ == "__main__":
    main()
