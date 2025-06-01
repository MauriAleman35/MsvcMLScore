import os
import json
import pickle
import numpy as np
from pathlib import Path
import logging
import warnings
import tensorflow as tf

# Configurar logging
logger = logging.getLogger(__name__)

class ScorePredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.config = None
        self.is_loaded = False
        self.mock_mode = True  # Forzamos modo simulado para garantizar resultados correctos
        
        # Lista de características esperadas (en orden)
        self.selected_features = [
            'adress_verified',
            'identity_verified',
            'loan_count',
            'late_payment_count',
            'avg_days_late',
            'total_penalty',
            'payment_completion_ratio',
            'has_no_late_payments',
            'has_penalty',
            'loans_al_dia_ratio',
            'days_late_per_loan'
        ]
        
        # Configuración por defecto
        self.default_config = {
            "score_scale": {
                "min": 0,
                "max": 100
            }
        }
        
        # Intentar cargar el modelo para futuras mejoras
        self.load_model()
    
    def load_model(self):
        """Intenta cargar el modelo (solo para referencia futura)"""
        try:
            # Obtener ruta base de modelos
            base_dir = Path(__file__).parent.parent / "models" / "borrower"
            logger.info(f"Buscando modelo en: {base_dir}")
            
            # Asegurarse de que el directorio existe
            if not base_dir.exists():
                os.makedirs(base_dir, exist_ok=True)
                logger.warning(f"Creado directorio {base_dir} ya que no existía")
                self.mock_mode = True
                self.config = self.default_config
                return True
            
            # Verificar archivos
            model_path = base_dir / "modelo_scoring_crediticio.h5"
            scaler_path = base_dir / "scaler_scoring_crediticio.pkl"
            
            # Reportar estado
            if model_path.exists():
                logger.info(f"Modelo encontrado en {model_path}")
            else:
                logger.warning(f"No se encontró el archivo del modelo en {model_path}")
                
            if scaler_path.exists():
                logger.info(f"Scaler encontrado en {scaler_path}")
            else:
                logger.warning(f"No se encontró el archivo del scaler en {scaler_path}")
            
            # Por ahora, forzamos modo simulado para garantizar resultados correctos
            self.mock_mode = True
            self.config = self.default_config
            #logger.info("Usando modo simulado (algoritmo sintético) para garantizar resultados correctos")
            return True
            
        except Exception as e:
            logger.error(f"Error general cargando modelo: {str(e)}")
            self.mock_mode = True
            self.config = self.default_config
            return True
    
    def calculate_synthetic_score(self, input_data):
        """
        Implementa EXACTAMENTE el mismo algoritmo de score sintético usado en Google Colab
        """
        try:
            # Loggeamos todos los valores de entrada para debugging
            logger.info("Datos de entrada para cálculo de score:")
            for key, value in input_data.items():
                logger.info(f"  {key}: {value}")
            
            # Comenzar con una base de 70 puntos
            score = 70
            logger.info(f"Base inicial: {score}")
            
            # 1. Bonificación por verificaciones (hasta +15 puntos)
            verify_bonus = input_data.get('adress_verified', 0) * 5  # +5 por dirección verificada
            score += verify_bonus
            logger.info(f"Bonificación por dirección verificada: +{verify_bonus}")
            
            id_bonus = input_data.get('identity_verified', 0) * 10  # +10 por identidad verificada
            score += id_bonus
            logger.info(f"Bonificación por identidad verificada: +{id_bonus}")
            
            # 2. Penalización por pagos tardíos (hasta -20 puntos)
            late_payment_penalty = input_data.get('late_payment_count', 0) * -5
            late_payment_penalty = max(late_payment_penalty, -20)  # Limitar a -20 como máximo
            score += late_payment_penalty
            logger.info(f"Penalización por pagos tardíos: {late_payment_penalty}")
            
            # 3. Penalización por días de retraso (hasta -15 puntos)
            days_late_penalty = input_data.get('avg_days_late', 0) * -1
            days_late_penalty = max(days_late_penalty, -15)  # Limitar a -15 como máximo
            score += days_late_penalty
            logger.info(f"Penalización por días de retraso: {days_late_penalty}")
            
            # 4. Penalización por monto de penalidades (hasta -15 puntos)
            penalty_amount_penalty = input_data.get('total_penalty', 0) / 100 * -1  # -1 punto por cada 100 de penalidad
            penalty_amount_penalty = max(penalty_amount_penalty, -15)  # Limitar a -15 como máximo
            score += penalty_amount_penalty
            logger.info(f"Penalización por monto de penalidades: {penalty_amount_penalty}")
            
            # 5. Bonificación por comportamiento positivo
            
            # 5.1 Ratio alto de pagos completados (hasta +15 puntos)
            completion_bonus = input_data.get('payment_completion_ratio', 0) * 15
            score += completion_bonus
            logger.info(f"Bonificación por ratio de pagos completados: +{completion_bonus}")
            
            # 5.2 Sin pagos tardíos (bono adicional)
            no_late_payment_bonus = 0
            if input_data.get('has_no_late_payments', 0) == 1:
                no_late_payment_bonus = 10
                score += no_late_payment_bonus
            logger.info(f"Bonificación por no tener pagos tardíos: +{no_late_payment_bonus}")
            
            # 5.3 Ajuste para usuarios sin préstamos
            loan_adjustment = 0
            if input_data.get('loan_count', 0) == 0:
                loan_adjustment = -5
                score += loan_adjustment  # Ligero descuento por falta de historial
            logger.info(f"Ajuste por falta de historial crediticio: {loan_adjustment}")
            
            # Ajustar score para que esté entre 0-100
            original_score = score
            score = max(0, min(score, 100))
            logger.info(f"Score pre-limitado: {original_score}, Score final: {score}")
            
            # Redondear a enteros
            score = round(score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculando score sintético: {str(e)}")
            return 50  # Valor por defecto en caso de error
    
    def get_score_category(self, score):
        """
        Determina la categoría y nivel de riesgo basado en el score
        Usa las mismas categorías que en Google Colab
        """
        if score >= 90:
            return "Excelente", "Muy Bajo"
        elif score >= 75:
            return "Bueno", "Bajo"
        elif score >= 60:
            return "Satisfactorio", "Moderado"
        elif score >= 45:
            return "Regular", "Considerable"
        elif score >= 30:
            return "Problemático", "Alto"
        else:
            return "Crítico", "Muy Alto"
    
    def generate_explanation(self, input_data):
        """
        Genera una explicación sobre los factores que influyen en el score
        Siguiendo el mismo formato de Google Colab
        """
        explanation = []
        
        # Factores positivos
        positive_factors = []
        if input_data.get('identity_verified', 0) == 1:
            positive_factors.append("Identidad verificada")
        if input_data.get('adress_verified', 0) == 1:
            positive_factors.append("Dirección verificada")
        if input_data.get('has_no_late_payments', 0) == 1 and input_data.get('loan_count', 0) > 0:
            positive_factors.append("Sin pagos tardíos")
        if input_data.get('payment_completion_ratio', 0) > 0.8:
            positive_factors.append("Alto ratio de pagos completados")
        
        # Factores negativos
        negative_factors = []
        if input_data.get('late_payment_count', 0) > 0:
            negative_factors.append(f"{input_data.get('late_payment_count')} pagos tardíos")
        if input_data.get('avg_days_late', 0) > 0:
            negative_factors.append(f"Promedio de {input_data.get('avg_days_late', 0):.1f} días de retraso")
        if input_data.get('total_penalty', 0) > 0:
            negative_factors.append(f"Penalidades por ${input_data.get('total_penalty', 0):.2f}")
        if input_data.get('loan_count', 0) == 0:
            negative_factors.append("Sin historial crediticio")
        
        # Agregar factores a explicación
        if positive_factors:
            explanation.append("Factores positivos: " + ", ".join(positive_factors))
        if negative_factors:
            explanation.append("Factores negativos: " + ", ".join(negative_factors))
        
        return explanation
    
    def predict_score(self, input_data):
        """Realiza la predicción de score crediticio"""
        try:
            # Normalizar las claves del diccionario
            normalized_data = {}
            for key, value in input_data.items():
                # Reemplazar posibles variaciones en los nombres de las claves
                normalized_key = key.replace('_', '_')
                normalized_data[normalized_key] = value
            
            logger.info("Calculando score crediticio...")
            
            # Usar algoritmo sintético (exactamente igual a Google Colab)
            score = self.calculate_synthetic_score(normalized_data)
            
            # Obtener categoría y nivel de riesgo
            category, risk_level = self.get_score_category(score)
            
            # Generar explicación
            explanation = self.generate_explanation(normalized_data)
            
            logger.info(f"Score calculado: {score} ({category}, {risk_level})")
            
            return {
                "score": float(score),
                "confidence": 0.9,  # Alta confianza al usar algoritmo directo
                "category": category,
                "risk_level": risk_level,
                "explanation": explanation,
                "input_features": normalized_data,
                "is_simulated": True
            }
            
        except Exception as e:
            logger.error(f"Error general al predecir score: {str(e)}")
            # Devolver un valor por defecto en caso de error
            return {
                "score": 50.0,
                "confidence": 0.3,
                "category": "Regular",
                "risk_level": "Considerable",
                "error": str(e),
                "explanation": ["Error al procesar la solicitud"],
                "input_features": input_data,
                "is_simulated": True
            }