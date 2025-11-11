WELCOME_STYLE = '''
<style>
body, html, #root {height:100%; margin:0; font-family:sans-serif;}
.welcome-container {
    position: relative;
    height: 100vh;
    width: 100vw;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: linear-gradient(120deg,#ff416c,#ff4b2b,#1f4037,#99f2c8);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    text-align: center;
    color: white;
}
@keyframes gradientBG {
0% {background-position:0% 50%;}
50% {background-position:100% 50%;}
100% {background-position:0% 50%;}
}
.welcome-title {font-size:4rem; font-weight:700; margin:0;}
.welcome-subtitle {font-size:1.8rem; margin-top:1rem; font-weight:400;}
.start-button {
    margin-top:2rem;
    padding:1rem 3rem;
    font-size:1.5rem;
    font-weight:600;
    border:none;
    border-radius:50px;
    cursor:pointer;
    background: linear-gradient(90deg,#1e3c72,#2a5298);
    color:white;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.start-button:hover {transform:scale(1.05); box-shadow:0 0 20px rgba(0,0,0,0.5);}
</style>
'''

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">😊 Keep Smiling Job Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-subtitle">Find your next job closer to home</div>', unsafe_allow_html=True)
    if st.button("🚀 Get Started", key="welcome_start"):
        st.session_state.welcome_done = True
    st.markdown('</div>', unsafe_allow_html=True)
