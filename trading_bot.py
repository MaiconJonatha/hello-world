#!/usr/bin/env python3
"""
Sistema de Trading Automatizado para Bolsa de Valores
Autor: Maicon Jonatha - Trading Bot AI
Data: 2025-11-16
Repositório: github.com/MaiconJonatha/hello-world

Este sistema permite:
- Monitorar preços de ações em tempo real
- Executar ordens de compra e venda automaticamente
- Gerenciar risco e stop loss
- Análise técnica básica (Médias Móveis, RSI)
- Estratégia de cruzamento de médias
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time


class TradingBot:
    """
    Bot de Trading Automatizado para Bolsa de Valores
    """
    
    def __init__(self, capital_inicial=10000, risco_por_trade=0.02):
        """
        Inicializa o bot de trading
        
        Args:
            capital_inicial: Capital disponível para trading (padrão: R$ 10,000)
            risco_por_trade: Porcentagem de risco por operação (padrão: 2%)
        """
        self.capital = capital_inicial
        self.capital_inicial = capital_inicial
        self.risco_por_trade = risco_por_trade
        self.posicoes = {}
        self.historico_trades = []
        print(f"✅ Trading Bot inicializado com capital de R$ {capital_inicial:,.2f}")
    
    def obter_preco_ativo(self, ticker):
        """
        Obtém o preço atual de um ativo
        
        Args:
            ticker: Símbolo do ativo (ex: 'PETR4.SA' para Petrobras)
            
        Returns:
            float: Preço atual do ativo ou None se houver erro
        """
        try:
            ativo = yf.Ticker(ticker)
            dados = ativo.history(period='1d')
            if not dados.empty:
                return dados['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"❌ Erro ao obter preço de {ticker}: {e}")
            return None
    
    def obter_dados_historicos(self, ticker, periodo='1mo'):
        """
        Obtém dados históricos de um ativo
        
        Args:
            ticker: Símbolo do ativo
            periodo: Período dos dados (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame: Dados históricos (Open, High, Low, Close, Volume)
        """
        try:
            ativo = yf.Ticker(ticker)
            return ativo.history(period=periodo)
        except Exception as e:
            print(f"❌ Erro ao obter dados históricos de {ticker}: {e}")
            return None
    
    def calcular_media_movel(self, dados, periodo=20):
        """
        Calcula média móvel simples (SMA)
        
        Args:
            dados: DataFrame com dados históricos
            periodo: Período da média móvel (padrão: 20 dias)
            
        Returns:
            Series: Média móvel calculada
        """
        return dados['Close'].rolling(window=periodo).mean()
    
    def calcular_rsi(self, dados, periodo=14):
        """
        Calcula o RSI (Relative Strength Index)
        
        Args:
            dados: DataFrame com dados históricos
            periodo: Período para cálculo do RSI (padrão: 14 dias)
            
        Returns:
            Series: RSI calculado (valores entre 0 e 100)
        """
        delta = dados['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
        rs = ganho / perda
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def comprar(self, ticker, quantidade, preco):
        """
        Executa ordem de compra
        
        Args:
            ticker: Símbolo do ativo
            quantidade: Quantidade de ações
            preco: Preço de compra
            
        Returns:
            bool: True se a compra foi bem-sucedida
        """
        custo_total = quantidade * preco
        
        if custo_total > self.capital:
            print(f"❌ Capital insuficiente para comprar {quantidade} de {ticker}")
            return False
        
        self.capital -= custo_total
        
        if ticker in self.posicoes:
            qtd_antiga = self.posicoes[ticker]['quantidade']
            preco_antigo = self.posicoes[ticker]['preco_medio']
            self.posicoes[ticker]['quantidade'] += quantidade
            self.posicoes[ticker]['preco_medio'] = (
                (preco_antigo * qtd_antiga + preco * quantidade) / 
                (qtd_antiga + quantidade)
            )
        else:
            self.posicoes[ticker] = {
                'quantidade': quantidade,
                'preco_medio': preco,
                'data_compra': datetime.now()
            }
        
        self.historico_trades.append({
            'tipo': 'COMPRA',
            'ticker': ticker,
            'quantidade': quantidade,
            'preco': preco,
            'data': datetime.now(),
            'total': custo_total
        })
        
        print(f"📈 COMPRA: {quantidade} {ticker} @ R$ {preco:.2f} = R$ {custo_total:,.2f}")
        return True
    
    def vender(self, ticker, quantidade, preco):
        """
        Executa ordem de venda
        
        Args:
            ticker: Símbolo do ativo
            quantidade: Quantidade de ações
            preco: Preço de venda
            
        Returns:
            bool: True se a venda foi bem-sucedida
        """
        if ticker not in self.posicoes:
            print(f"❌ Não há posição em {ticker}")
            return False
        
        if self.posicoes[ticker]['quantidade'] < quantidade:
            print(f"❌ Quantidade insuficiente de {ticker}")
            return False
        
        valor_venda = quantidade * preco
        self.capital += valor_venda
        
        preco_medio = self.posicoes[ticker]['preco_medio']
        lucro = (preco - preco_medio) * quantidade
        lucro_pct = ((preco / preco_medio) - 1) * 100
        
        self.posicoes[ticker]['quantidade'] -= quantidade
        
        if self.posicoes[ticker]['quantidade'] == 0:
            del self.posicoes[ticker]
        
        self.historico_trades.append({
            'tipo': 'VENDA',
            'ticker': ticker,
            'quantidade': quantidade,
            'preco': preco,
            'data': datetime.now(),
            'total': valor_venda,
            'lucro': lucro,
            'lucro_pct': lucro_pct
        })
        
        print(f"📉 VENDA: {quantidade} {ticker} @ R$ {preco:.2f} = R$ {valor_venda:,.2f}")
        print(f"💹 Lucro: R$ {lucro:.2f} ({lucro_pct:+.2f}%)")
        return True

            def estrategia_cruzamento_medias(self, ticker, periodo_curto=20, periodo_longo=50):
        """
        Estratégia baseada no cruzamento de médias móveis.
        Compra quando média curta cruza acima da longa.
        Vende quando média curta cruza abaixo da longa.
        """
        dados = self.obter_dados_historicos(ticker, periodo=periodo_longo + 10)
        if dados is None or len(dados) < periodo_longo:
            return None
        
        media_curta = self.calcular_media_movel(dados, periodo_curto)
        media_longa = self.calcular_media_movel(dados, periodo_longo)
        preco_atual = self.obter_preco_ativo(ticker)
        
        if preco_atual is None:
            return None
        
        # Verifica cruzamento
        if media_curta[-1] > media_longa[-1] and media_curta[-2] <= media_longa[-2]:
            return 'COMPRAR'
        elif media_curta[-1] < media_longa[-1] and media_curta[-2] >= media_longa[-2]:
            return 'VENDER'
        
        return 'MANTER'
    
    def estrategia_rsi(self, ticker, periodo=14, limite_sobrecompra=70, limite_sobrevenda=30):
        """
        Estratégia baseada no RSI (Índice de Força Relativa).
        Compra quando RSI está abaixo do limite de sobrevenda.
        Vende quando RSI está acima do limite de sobrecompra.
        """
        dados = self.obter_dados_historicos(ticker, periodo=periodo + 10)
        if dados is None or len(dados) < periodo:
            return None
        
        rsi = self.calcular_rsi(dados, periodo)
        if rsi is None or len(rsi) == 0:
            return None
        
        rsi_atual = rsi[-1]
        
        if rsi_atual < limite_sobrevenda:
            return 'COMPRAR'
        elif rsi_atual > limite_sobrecompra:
            return 'VENDER'
        
        return 'MANTER'

            
    def monitorar_posicoes(self):
        """
        Monitora as posicoes abertas e exibe relatorio.
        """
        if not self.posicoes:
            print("\n Nenhuma posicao aberta no momento.")
            return
        
        print("\n" + "="*70)
        print(" RELATORIO DE POSICOES ABERTAS")
        print("="*70)
        
        valor_total_posicoes = 0
        lucro_total_nao_realizado = 0
        
        for ticker, info in self.posicoes.items():
            preco_atual = self.obter_preco_ativo(ticker)
            if preco_atual is None:
                continue
            
            quantidade = info['quantidade']
            preco_medio = info['preco_medio']
            valor_investido = quantidade * preco_medio
            valor_atual = quantidade * preco_atual
            lucro_nao_realizado = valor_atual - valor_investido
            lucro_pct = (lucro_nao_realizado / valor_investido) * 100
            
            valor_total_posicoes += valor_atual
            lucro_total_nao_realizado += lucro_nao_realizado
            
            print(f"\n {ticker}:")
            print(f"   Quantidade: {quantidade} acoes")
            print(f"   Preco Medio: R$ {preco_medio:.2f}")
            print(f"   Preco Atual: R$ {preco_atual:.2f}")
            print(f"   Valor Investido: R$ {valor_investido:.2f}")
            print(f"   Valor Atual: R$ {valor_atual:.2f}")
            print(f"   Lucro Nao Realizado: R$ {lucro_nao_realizado:.2f} ({lucro_pct:+.2f}%)")
        
        print("\n" + "="*70)
        print(f" Capital Disponivel: R$ {self.capital:.2f}")
        print(f" Valor Total em Posicoes: R$ {valor_total_posicoes:.2f}")
        print(f" Lucro Total Nao Realizado: R$ {lucro_total_nao_realizado:.2f}")
        print(f" Patrimonio Total: R$ {self.capital + valor_total_posicoes:.2f}")
        print("="*70)

            
    def exibir_historico(self):
        """
        Exibe o historico de todas as operacoes realizadas.
        """
        if not self.historico_trades:
            print("\n Nenhuma operacao realizada ainda.")
            return
        
        print("\n" + "="*70)
        print(" HISTORICO DE OPERACOES")
        print("="*70)
        
        for i, trade in enumerate(self.historico_trades, 1):
            print(f"\nOperacao #{i}:")
            print(f"  Tipo: {trade['tipo']}")
            print(f"  Ticker: {trade['ticker']}")
            print(f"  Quantidade: {trade['quantidade']}")
            print(f"  Preco: R$ {trade['preco']:.2f}")
            print(f"  Total: R$ {trade['total']:.2f}")
            print(f"  Data: {trade['data']}")
            
            if 'lucro' in trade:
                print(f"  Lucro: R$ {trade['lucro']:.2f} ({trade['lucro_pct']:+.2f}%)")
        
        print("\n" + "="*70)
    
    def rodar_bot(self, tickers, estrategia='cruzamento_medias', intervalo=60):
        """
        Executa o bot de trading continuamente.
        
        Parametros:
        - tickers: lista de ativos para monitorar
        - estrategia: 'cruzamento_medias' ou 'rsi'
        - intervalo: tempo em segundos entre cada verificacao
        """
        print(" BOT DE TRADING INICIADO")
        print(f"Monitorando: {', '.join(tickers)}")
        print(f"Estrategia: {estrategia}")
        print(f"Capital inicial: R$ {self.capital:.2f}")
        print("\nPressione Ctrl+C para parar o bot\n")
        
        try:
            while True:
                for ticker in tickers:
                    if estrategia == 'cruzamento_medias':
                        sinal = self.estrategia_cruzamento_medias(ticker)
                    elif estrategia == 'rsi':
                        sinal = self.estrategia_rsi(ticker)
                    else:
                        print(f"Estrategia '{estrategia}' nao reconhecida.")
                        return
                    
                    if sinal == 'COMPRAR':
                        preco = self.obter_preco_ativo(ticker)
                        if preco:
                            # Compra 10 acoes por vez
                            self.comprar(ticker, 10, preco)
                    
                    elif sinal == 'VENDER' and ticker in self.posicoes:
                        preco = self.obter_preco_ativo(ticker)
                        quantidade = self.posicoes[ticker]['quantidade']
                        if preco:
                            self.vender(ticker, quantidade, preco)
                
                time.sleep(intervalo)
        
        except KeyboardInterrupt:
            print("\n\n Bot interrompido pelo usuario.")
            self.monitorar_posicoes()
            self.exibir_historico()


            # Exemplo de uso
if __name__ == "__main__":
    # Cria o bot com capital inicial de R$ 10.000
    bot = TradingBot(capital_inicial=10000.0)
    
    # Lista de acoes da B3 para monitorar
    acoes_b3 = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA']
    
    print(" BOT DE TRADING - BOLSA DE VALORES B3")
    print("="*70)
    print("\nEscolha uma opcao:")
    print("1 - Consultar preco de uma acao")
    print("2 - Comprar acoes")
    print("3 - Vender acoes")
    print("4 - Ver posicoes abertas")
    print("5 - Ver historico de operacoes")
    print("6 - Executar estrategia de cruzamento de medias")
    print("7 - Executar estrategia RSI")
    print("8 - Rodar bot automatico")
    print("0 - Sair")
    
    while True:
        try:
            opcao = input("\nDigite a opcao desejada: ")
            
            if opcao == '1':
                ticker = input("Digite o ticker da acao (ex: PETR4.SA): ").upper()
                preco = bot.obter_preco_ativo(ticker)
                if preco:
                    print(f"\n Preco atual de {ticker}: R$ {preco:.2f}")
            
            elif opcao == '2':
                ticker = input("Digite o ticker da acao: ").upper()
                quantidade = int(input("Digite a quantidade: "))
                preco = bot.obter_preco_ativo(ticker)
                if preco:
                    print(f"Preco atual: R$ {preco:.2f}")
                    confirma = input("Confirmar compra? (s/n): ")
                    if confirma.lower() == 's':
                        bot.comprar(ticker, quantidade, preco)
            
            elif opcao == '3':
                if not bot.posicoes:
                    print("\n Voce nao possui acoes para vender.")
                else:
                    print("\nAcoes disponiveis:")
                    for ticker in bot.posicoes.keys():
                        print(f"  - {ticker}")
                    ticker = input("\nDigite o ticker da acao: ").upper()
                    if ticker in bot.posicoes:
                        quantidade = int(input("Digite a quantidade: "))
                        preco = bot.obter_preco_ativo(ticker)
                        if preco:
                            print(f"Preco atual: R$ {preco:.2f}")
                            confirma = input("Confirmar venda? (s/n): ")
                            if confirma.lower() == 's':
                                bot.vender(ticker, quantidade, preco)
                    else:
                        print(f"\n Voce nao possui acoes de {ticker}")
            
            elif opcao == '4':
                bot.monitorar_posicoes()
            
            elif opcao == '5':
                bot.exibir_historico()
            
            elif opcao == '6':
                ticker = input("Digite o ticker da acao: ").upper()
                sinal = bot.estrategia_cruzamento_medias(ticker)
                if sinal:
                    print(f"\n Sinal: {sinal}")
            
            elif opcao == '7':
                ticker = input("Digite o ticker da acao: ").upper()
                sinal = bot.estrategia_rsi(ticker)
                if sinal:
                    print(f"\n Sinal: {sinal}")
            
            elif opcao == '8':
                print("\nAcoes disponiveis:")
                for acao in acoes_b3:
                    print(f"  - {acao}")
                
                tickers_input = input("\nDigite os tickers separados por virgula (ou Enter para usar todas): ")
                if tickers_input.strip():
                    tickers = [t.strip().upper() for t in tickers_input.split(',')]
                else:
                    tickers = acoes_b3
                
                print("\nEstrategias disponiveis:")
                print("  1 - cruzamento_medias")
                print("  2 - rsi")
                estrategia_opt = input("Escolha a estrategia (1 ou 2): ")
                
                if estrategia_opt == '1':
                    estrategia = 'cruzamento_medias'
                elif estrategia_opt == '2':
                    estrategia = 'rsi'
                else:
                    print(" Opcao invalida!")
                    continue
                
                intervalo = input("Intervalo entre verificacoes em segundos (padrao 60): ")
                intervalo = int(intervalo) if intervalo.strip() else 60
                
                bot.rodar_bot(tickers, estrategia, intervalo)
            
            elif opcao == '0':
                print("\n Encerrando bot...")
                bot.monitorar_posicoes()
                print("\n Obrigado por usar o Bot de Trading!")
                break
            
            else:
                print(" Opcao invalida! Tente novamente.")
        
        except KeyboardInterrupt:
            print("\n\n Bot interrompido pelo usuario.")
            bot.monitorar_posicoes()
            break
        except Exception as e:
            print(f"\n Erro: {e}")
            print("Tente novamente.")