from config import Config
from supabase import create_client
import gotrue.errors

def create_test_user():
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    supabase = create_client(url, key)

    email = "admin@teste.com"
    password = "password123"

    print(f"Tentando criar usuário: {email}")
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print("Usuário criado com sucesso!")
        print(f"Email: {email}")
        print(f"Senha: {password}")
        print("Verifique se o email requer confirmação no dashboard do Supabase (por padrão sim, mas em alguns setups dev pode não precisar).")
        
        if res.user and res.user.identities and len(res.user.identities) > 0:
             print("User ID:", res.user.id)
        else:
             print("Aviso: Usuário criado mas pode já existir ou requerer confirmação.")

    except gotrue.errors.AuthApiError as e:
        print(f"Erro da API de Auth: {e.message}")
        if "User already registered" in str(e) or "already registered" in str(e).lower():
            print(f"O usuário {email} já existe. Pode usar a senha definida anteriormente (se não mudou, tente '{password}').")
    except Exception as e:
        print(f"Erro ao criar usuário: {str(e)}")

if __name__ == "__main__":
    create_test_user()
