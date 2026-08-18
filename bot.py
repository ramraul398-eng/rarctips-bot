def preguntar_groq(mensaje):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "Eres Valentina, cariñosa."},
                {"role": "user", "content": mensaje}
            ]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        data = r.json()
        if "choices" not in data:
            print(f"GROQ ERROR COMPLETO: {data}")
            return f"Groq me dijo: {data}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"ERROR GROQ: {e}")
        return f"Error: {e}"
