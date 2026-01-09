#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0069
"""
Currency Strength Calculator - Enterprise Edition
Advanced currency strength analysis with BaseEnterpriseService integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

from services.common.base_service import BaseEnterpriseService


class StrengthTimeframe(Enum):
    """Currency strength calculation timeframes"""
    M1 = "1M"
    M5 = "5M"
    M15 = "15M"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"


@dataclass
class CurrencyStrengthData:
    """Currency strength calculation result"""
    currency: str
    strength_score: float
    rank: int
    timestamp: datetime
    timeframe: StrengthTimeframe
    contributing_pairs: List[str]
    metadata: Dict[str, Any]


class CurrencyStrengthCalculator:
    """
    Advanced currency strength calculator with multi-timeframe analysis
    Integrates with EAFIX trading system P_GUI specifications
    """

    def __init__(self, major_currencies: List[str] = None):
        self.logger = logging.getLogger(__name__)

        # Major currencies for strength analysis
        self.major_currencies = major_currencies or [
            "USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"
        ]

        # Currency pair combinations
        self.currency_pairs = self._generate_currency_pairs()

        # Strength calculation parameters
        self.lookback_periods = {
            StrengthTimeframe.M1: 60,    # 1 hour
            StrengthTimeframe.M5: 60,    # 5 hours
            StrengthTimeframe.M15: 60,   # 15 hours
            StrengthTimeframe.H1: 24,    # 1 day
            StrengthTimeframe.H4: 24,    # 4 days
            StrengthTimeframe.D1: 30,    # 30 days
        }

    def _generate_currency_pairs(self) -> List[str]:
        """Generate all major currency pair combinations"""
        pairs = []
        for i, base in enumerate(self.major_currencies):
            for quote in self.major_currencies[i+1:]:
                pairs.extend([f"{base}{quote}", f"{quote}{base}"])
        return pairs

    async def calculate_strength(
        self,
        price_data: Dict[str, pd.DataFrame],
        timeframe: StrengthTimeframe = StrengthTimeframe.H1,
        method: str = "roc"  # Rate of Change method
    ) -> List[CurrencyStrengthData]:
        """
        Calculate currency strength scores for all major currencies

        Args:
            price_data: Dictionary of currency pair DataFrames with OHLC data
            timeframe: Timeframe for strength calculation
            method: Calculation method ("roc", "momentum", "correlation")

        Returns:
            List of CurrencyStrengthData sorted by strength score
        """
        try:
            self.logger.info(f"Calculating currency strength for {timeframe.value} timeframe")

            # Initialize strength scores
            strength_scores = {currency: 0.0 for currency in self.major_currencies}
            pair_counts = {currency: 0 for currency in self.major_currencies}

            # Calculate strength for each currency
            for pair, data in price_data.items():
                if len(pair) != 6 or pair not in self.currency_pairs:
                    continue

                base_currency = pair[:3]
                quote_currency = pair[3:]

                if base_currency not in self.major_currencies or quote_currency not in self.major_currencies:
                    continue

                # Calculate pair strength contribution
                strength_contribution = await self._calculate_pair_strength(
                    data, timeframe, method
                )

                # Apply strength to currencies
                if strength_contribution is not None:
                    strength_scores[base_currency] += strength_contribution
                    strength_scores[quote_currency] -= strength_contribution
                    pair_counts[base_currency] += 1
                    pair_counts[quote_currency] += 1

            # Normalize strength scores
            normalized_scores = {}
            for currency in self.major_currencies:
                if pair_counts[currency] > 0:
                    normalized_scores[currency] = strength_scores[currency] / pair_counts[currency]
                else:
                    normalized_scores[currency] = 0.0

            # Create strength data objects
            current_time = datetime.utcnow()
            strength_results = []

            # Sort by strength score and assign ranks
            sorted_currencies = sorted(
                normalized_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            for rank, (currency, score) in enumerate(sorted_currencies, 1):
                contributing_pairs = [
                    pair for pair in self.currency_pairs
                    if pair.startswith(currency) or pair.endswith(currency)
                ]

                strength_data = CurrencyStrengthData(
                    currency=currency,
                    strength_score=score,
                    rank=rank,
                    timestamp=current_time,
                    timeframe=timeframe,
                    contributing_pairs=contributing_pairs[:10],  # Limit to top 10
                    metadata={
                        "method": method,
                        "pair_count": pair_counts[currency],
                        "raw_score": strength_scores[currency]
                    }
                )
                strength_results.append(strength_data)

            self.logger.info(f"Currency strength calculation completed: {len(strength_results)} currencies analyzed")
            return strength_results

        except Exception as e:
            self.logger.error(f"Currency strength calculation failed: {e}")
            raise

    async def _calculate_pair_strength(
        self,
        pair_data: pd.DataFrame,
        timeframe: StrengthTimeframe,
        method: str
    ) -> Optional[float]:
        """Calculate strength contribution for a single currency pair"""
        try:
            if pair_data.empty or len(pair_data) < 2:
                return None

            lookback = self.lookback_periods.get(timeframe, 24)
            recent_data = pair_data.tail(lookback)

            if method == "roc":
                # Rate of Change method
                if len(recent_data) < 2:
                    return None

                start_price = recent_data.iloc[0]['close']
                end_price = recent_data.iloc[-1]['close']

                if start_price == 0:
                    return None

                roc = (end_price - start_price) / start_price * 100
                return roc

            elif method == "momentum":
                # Momentum method
                if len(recent_data) < lookback:
                    return None

                momentum = recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]
                normalized_momentum = momentum / recent_data['close'].iloc[0] * 100
                return normalized_momentum

            elif method == "correlation":
                # Correlation-based method (placeholder)
                # This would require additional market data for correlation analysis
                return 0.0

            else:
                self.logger.warning(f"Unknown strength calculation method: {method}")
                return None

        except Exception as e:
            self.logger.error(f"Pair strength calculation failed: {e}")
            return None

    async def get_strength_matrix(
        self,
        price_data: Dict[str, pd.DataFrame],
        timeframes: List[StrengthTimeframe] = None
    ) -> Dict[str, List[CurrencyStrengthData]]:
        """
        Get currency strength matrix across multiple timeframes

        Returns:
            Dictionary mapping timeframe to strength results
        """
        if timeframes is None:
            timeframes = [StrengthTimeframe.M15, StrengthTimeframe.H1, StrengthTimeframe.H4]

        strength_matrix = {}

        for timeframe in timeframes:
            try:
                strength_results = await self.calculate_strength(price_data, timeframe)
                strength_matrix[timeframe.value] = strength_results
            except Exception as e:
                self.logger.error(f"Failed to calculate strength for {timeframe.value}: {e}")
                strength_matrix[timeframe.value] = []

        return strength_matrix

    def get_strongest_pairs(
        self,
        strength_results: List[CurrencyStrengthData],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get strongest currency pairs based on strength differential

        Args:
            strength_results: Currency strength calculation results
            top_n: Number of top pairs to return

        Returns:
            List of strongest pairs with strength differential
        """
        pair_strengths = []

        # Sort by strength
        sorted_currencies = sorted(strength_results, key=lambda x: x.strength_score, reverse=True)

        # Generate pairs by combining strong and weak currencies
        for i, strong_currency in enumerate(sorted_currencies[:4]):  # Top 4 strong
            for weak_currency in sorted_currencies[-4:]:  # Bottom 4 weak
                if strong_currency.currency != weak_currency.currency:
                    strength_diff = strong_currency.strength_score - weak_currency.strength_score

                    pair_info = {
                        "pair": f"{strong_currency.currency}{weak_currency.currency}",
                        "strength_differential": strength_diff,
                        "strong_currency": strong_currency.currency,
                        "weak_currency": weak_currency.currency,
                        "strong_score": strong_currency.strength_score,
                        "weak_score": weak_currency.strength_score,
                        "timestamp": strong_currency.timestamp
                    }
                    pair_strengths.append(pair_info)

        # Sort by strength differential and return top N
        pair_strengths.sort(key=lambda x: x["strength_differential"], reverse=True)
        return pair_strengths[:top_n]


class CurrencyStrengthService(BaseEnterpriseService):
    """Enterprise currency strength calculation service"""

    def __init__(self):
        super().__init__(service_name="currency-strength")
        self.calculator = CurrencyStrengthCalculator()
        self.current_strength_data = {}
        self.logger = logging.getLogger(__name__)

    async def startup(self):
        """Initialize currency strength service"""
        self.logger.info("Starting currency strength calculation service...")

    async def shutdown(self):
        """Graceful shutdown of currency strength service"""
        self.logger.info("Shutting down currency strength service...")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for currency strength service"""
        return {
            "service": "currency-strength",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "calculator": "healthy",
                "currencies_tracked": len(self.calculator.major_currencies),
                "pairs_tracked": len(self.calculator.currency_pairs)
            }
        }

    async def calculate_current_strength(
        self,
        price_data: Dict[str, pd.DataFrame],
        timeframe: str = "1H"
    ) -> Dict[str, Any]:
        """Calculate current currency strength and cache results"""
        try:
            timeframe_enum = StrengthTimeframe(timeframe)
            strength_results = await self.calculator.calculate_strength(
                price_data, timeframe_enum
            )

            # Cache results
            self.current_strength_data[timeframe] = strength_results

            # Update metrics
            self.metrics.request_count.labels(
                method="calculate",
                endpoint="strength",
                status="success"
            ).inc()

            return {
                "success": True,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
                "currencies": [
                    {
                        "currency": result.currency,
                        "strength_score": result.strength_score,
                        "rank": result.rank
                    }
                    for result in strength_results
                ]
            }

        except Exception as e:
            self.metrics.request_count.labels(
                method="calculate",
                endpoint="strength",
                status="error"
            ).inc()
            self.logger.error(f"Currency strength calculation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }