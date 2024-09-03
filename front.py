# frontend.py

def get_styles():
    return """
    <style>
    .main {
        background-color: white;
    }
    .gray-text {
        color: gray;
    }
    .stTextInput > div > div > input {
        background-color: #F0F2F6;
    }
    </style>
    """

def get_header():
    return """
    <div style="text-align: center;">
        <h1 style="color: #0184FF;">토독토독</h1>
    </div>
    """

def display_message(sender, message):
    if sender == "You":
        return f'''
        <div style="
            background-color: #007BFF; 
            color: white; 
            padding: 10px; 
            border-radius: 20px; 
            margin: 5px 0; 
            max-width: 70%; 
            float: right; 
            clear: both; 
            word-wrap: break-word;
            box-shadow: 0px 2px 12px rgba(0, 123, 255, 0.5);
        ">
            {message}
        </div>
        <div style="clear: both;"></div>
        '''
    else:
        return f'''
        <div style="
            background-color: #F1F1F1; 
            color: black; 
            padding: 10px; 
            border-radius: 20px; 
            margin: 5px 0; 
            max-width: 70%; 
            float: left; 
            clear: both; 
            word-wrap: break-word;
            box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.1);
        ">
            {message}
        </div>
        <div style="clear: both;"></div>
        '''
