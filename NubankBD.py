import mysql.connector
import re
from decimal import Decimal
from datetime import datetime

def limpar_cpf(cpf):
    return re.sub(r'\D', '', cpf)

class Banco:
    def __init__(self):
        self.conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="sistema_banco"
        )
        self.cursor = self.conexao.cursor()

    def criar_pessoa(self, nome, rg, data_nasc, email, telefone, cpf):
        cpf = limpar_cpf(cpf)

        data_nasc_formatada = datetime.strptime(data_nasc, "%d-%m-%Y").date()

        sql = "INSERT INTO Pessoa (nome, rg, data_nasc, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (nome, rg, data_nasc_formatada, email, telefone, cpf)
        try:
            self.cursor.execute(sql, valores)
            self.conexao.commit()
            print("Dados inseridos com sucesso.")
            return f"Pessoa {nome} criada com sucesso."
        except mysql.connector.Error as err:
            print(f"Erro ao criar pessoa: {err}")
            return f"Erro ao criar pessoa: {err}"

    def criar_conta(self, cpf):
        cpf = limpar_cpf(cpf)

        sql = "INSERT INTO Conta (cpf) VALUES (%s)"
        try:
            self.cursor.execute(sql, (cpf,))
            self.conexao.commit()
            return f"Conta criada com sucesso para o CPF: {cpf}."
        except mysql.connector.Error as err:
            print(f"Erro ao criar conta: {err}")
            return f"Erro ao criar conta: {err}"

    def consultar_pessoa(self, cpf):
        cpf = limpar_cpf(cpf)
        sql = "SELECT nome, rg, DATE_FORMAT(data_nasc, '%d-%m-%Y'), email, telefone FROM Pessoa WHERE cpf = %s"
        try:
            self.cursor.execute(sql, (cpf,))
            resultado = self.cursor.fetchone()
            if resultado:
                return resultado
            else:
                return None
        except mysql.connector.Error as err:
            print(f"Erro ao consultar pessoa: {err}")
            return None

    def consultar_saldo(self, cpf):
        cpf = limpar_cpf(cpf)
        sql = "SELECT saldo FROM Conta WHERE cpf = %s"
        try:
            self.cursor.execute(sql, (cpf,))
            resultado = self.cursor.fetchone()
            if resultado:
                return Decimal(resultado[0])
            else:
                return None
        except mysql.connector.Error as err:
            print(f"Erro ao consultar saldo: {err}")
            return None

    def atualizar_saldo(self, cpf, valor, tipo_transacao):
        cpf = limpar_cpf(cpf)
        saldo_atual = self.consultar_saldo(cpf)
        if saldo_atual is None:
            return "Conta não encontrada."

        valor_decimal = Decimal(valor)

        if tipo_transacao == 'deposito':
            saldo_novo = saldo_atual + valor_decimal
        elif tipo_transacao == 'saque':
            if saldo_atual >= valor_decimal:
                saldo_novo = saldo_atual - valor_decimal
            else:
                return "Saldo insuficiente."
        else:
            return "Tipo de transação inválido."

        sql_update_saldo = "UPDATE Conta SET saldo = %s WHERE cpf = %s"
        try:
            self.cursor.execute(sql_update_saldo, (saldo_novo, cpf))
            self.conexao.commit()

            sql_buscar_conta_id = "SELECT id FROM Conta WHERE cpf = %s"
            self.cursor.execute(sql_buscar_conta_id, (cpf,))
            conta_id = self.cursor.fetchone()[0]

            sql_registrar_movimentacao = """
                INSERT INTO movimentacao_conta (conta_id, cpf, tipo_transacao, valor)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(sql_registrar_movimentacao, (conta_id, cpf, tipo_transacao, valor_decimal))
            self.conexao.commit()

            return f"Saldo atualizado com sucesso: {saldo_novo:.2f}. Movimentação registrada."
        except mysql.connector.Error as err:
            return f"Erro ao atualizar saldo: {err}"

    def remover_conta(self, cpf):
        cpf = limpar_cpf(cpf)
        sql = "DELETE FROM Conta WHERE cpf = %s"
        try:
            self.cursor.execute(sql, (cpf,))
            self.conexao.commit()
            return f"Conta removida com sucesso para o CPF: {cpf}."
        except mysql.connector.Error as err:
            print(f"Erro ao remover conta: {err}")
            return f"Erro ao remover conta: {err}"

    def atualizar_dados_pessoa(self, cpf, nome=None, rg=None, data_nasc=None, email=None, telefone=None):
        cpf = limpar_cpf(cpf)
        set_clause = []
        values = []

        if nome:
            set_clause.append("nome = %s")
            values.append(nome)
        if rg:
            set_clause.append("rg = %s")
            values.append(rg)
        if data_nasc:
            data_nasc_formatada = datetime.strptime(data_nasc, "%d-%m-%Y").date()
            set_clause.append("data_nasc = %s")
            values.append(data_nasc_formatada)
        if email:
            set_clause.append("email = %s")
            values.append(email)
        if telefone:
            set_clause.append("telefone = %s")
            values.append(telefone)

        if not set_clause:
            return "Nenhum dado para atualizar."

        sql = f"UPDATE Pessoa SET {', '.join(set_clause)} WHERE cpf = %s"
        values.append(cpf)

        try:
            self.cursor.execute(sql, tuple(values))
            self.conexao.commit()
            return f"Dados atualizados com sucesso para o CPF: {cpf}."
        except mysql.connector.Error as err:
            return f"Erro ao atualizar dados: {err}"

    def consultar_movimentacoes(self, cpf):
        cpf = limpar_cpf(cpf)
        sql = """
            SELECT tipo_transacao, valor, DATE_FORMAT(data_hora, '%d-%m-%Y %H:%i')
            FROM movimentacao_conta
            WHERE cpf = %s
        """
        try:
            self.cursor.execute(sql, (cpf,))
            movimentacoes = self.cursor.fetchall()

            if movimentacoes:
                for mov in movimentacoes:
                    print(f"Tipo: {mov[0]}, Valor: {mov[1]:.2f}, Data/Hora: {mov[2]}")
                return f"{len(movimentacoes)} movimentações encontradas."
            else:
                return "Nenhuma movimentação encontrada."
        except mysql.connector.Error as err:
            return f"Erro ao consultar movimentações: {err}"

def main():
    banco = Banco()

    while True:
        print("\n== SISTEMA BANCÁRIO NUBANK ==")
        print("1. Criar Pessoa")
        print("2. Criar Conta")
        print("3. Consultar Pessoa")
        print("4. Atualizar Dados da Pessoa")
        print("5. Atualizar Saldo")
        print("6. Consultar Saldo")
        print("7. Consultar Movimentações")
        print("8. Remover Conta")
        print("9. Sair")

        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            nome = input("Nome: ")
            rg = input("RG: ")
            data_nasc = input("Data de Nascimento (DD-MM-YYYY): ")
            email = input("Email: ")
            telefone = input("Telefone: ")
            cpf = input("CPF: ")
            print(banco.criar_pessoa(nome, rg, data_nasc, email, telefone, cpf))

        elif escolha == '2':
            cpf = input("CPF: ")
            print(banco.criar_conta(cpf))

        elif escolha == '3':
            cpf = input("CPF: ")
            pessoa = banco.consultar_pessoa(cpf)
            if pessoa:
                print(f"Nome: {pessoa[0]}, RG: {pessoa[1]}, Data de Nascimento: {pessoa[2]}, Email: {pessoa[3]}, Telefone: {pessoa[4]}")
            else:
                print("Pessoa não encontrada.")

        elif escolha == '4':
            cpf = input("CPF: ")
            nome = input("Novo Nome (deixe vazio se não quiser alterar): ")
            rg = input("Novo RG (deixe vazio se não quiser alterar): ")
            data_nasc = input("Nova Data de Nascimento (DD-MM-YYYY) (deixe vazio se não quiser alterar): ")
            email = input("Novo Email (deixe vazio se não quiser alterar): ")
            telefone = input("Novo Telefone (deixe vazio se não quiser alterar): ")
            print(banco.atualizar_dados_pessoa(cpf, nome or None, rg or None, data_nasc or None, email or None, telefone or None))

        elif escolha == '5':
            cpf = input("CPF: ")
            valor = input("Valor: ")
            tipo_transacao = input("Tipo de Transação (deposito/saque): ")
            print(banco.atualizar_saldo(cpf, valor, tipo_transacao))

        elif escolha == '6':
            cpf = input("CPF: ")
            saldo = banco.consultar_saldo(cpf)
            if saldo is not None:
                print(f"Saldo atual: {saldo:.2f}")
            else:
                print("Conta não encontrada.")

        elif escolha == '7':
            cpf = input("CPF: ")
            print(banco.consultar_movimentacoes(cpf))

        elif escolha == '8':
            cpf = input("CPF: ")
            print(banco.remover_conta(cpf))

        elif escolha == '9':
            print("Saindo do sistema.")
            break

        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
