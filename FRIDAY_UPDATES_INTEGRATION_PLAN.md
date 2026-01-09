---
doc_id: DOC-CONFIG-0052
---

# Friday Morning Updates Integration Plan

## Overview
This document outlines the integration of four major update packages into the eafix-modular trading system:

1. **Testing Framework Enhancements** (UPDARE P_Testing_signal)
2. **Economic Calendar Automation** (UPDATE_Economic_calendar)
3. **Currency Strength Indicators** (UPDATEP_Currency strengthen indicator)
4. **Dashboard System Upgrades** (UPDATP_Python_huey P_dashboard)

## Integration Strategy

### Phase 1: Testing Framework Integration ✅
**Target**: Enhanced signal testing and validation capabilities

#### Files to Integrate:
- `signal_flow_tester.py` → `tests/integration/`
- `manual_testing_control_panel.py` → `P_GUI/testing/`
- `calendar_event_simulator.py` → `tests/fixtures/`
- `indicator_signal_simulator.py` → `tests/fixtures/`

#### Implementation Steps:
1. Create `tests/integration/` directory structure
2. Add testing framework to existing test suite
3. Integrate with current Makefile test targets
4. Update CI/CD pipeline to use new testing tools

### Phase 2: Economic Calendar Automation ✅
**Target**: Automated ForexFactory calendar downloading and processing

#### Files to Integrate:
- `ff_auto_downloader.py` → `services/calendar-downloader/src/` (already exists - enhance)
- `python_calendar_system_patched.py` → `services/calendar-downloader/src/` (already exists - merge)
- Calendar enhancement plan → `services/calendar-downloader/docs/`

#### Implementation Steps:
1. Merge enhancements with existing calendar service
2. Add automated scheduling and circuit breakers
3. Integrate with MT4 CSV bridge
4. Add comprehensive error handling and recovery

### Phase 3: Currency Strength Indicators ⏳
**Target**: Advanced currency strength analysis and visualization

#### Files to Integrate:
- DDE + Currency Strength Tab spec → `P_GUI/indicators/`
- Currency strength PyQt6 components → `P_GUI/widgets/`
- Backtesting framework → `services/backtesting/`

#### Implementation Steps:
1. Create new indicator service for currency strength
2. Build PyQt6 dashboard components
3. Integrate with existing DDE price feeds
4. Add multi-timeframe analysis capabilities

### Phase 4: Dashboard System Upgrades ⏳
**Target**: Scalable dashboard for 500+ signals with real-time updates

#### Files to Integrate:
- `dashboard_backend.py` → `services/dashboard/src/`
- `tkinter_dashboard_gui.py` → `P_GUI/dashboard/`
- `advanced_indicators.py` → `services/indicators/`
- Integration guide → `docs/integration/`

#### Implementation Steps:
1. Create new dashboard microservice
2. Integrate with existing indicator systems
3. Add SQLite persistence layer
4. Build plugin architecture for custom indicators

## Directory Structure After Integration

```
eafix-modular/
├── services/
│   ├── calendar-downloader/        # Enhanced with automation
│   ├── calendar-ingestor/          # Existing
│   ├── dashboard/                  # NEW - Dashboard backend
│   │   ├── src/
│   │   │   ├── dashboard_backend.py
│   │   │   ├── advanced_indicators.py
│   │   │   └── api.py
│   │   └── database/
│   ├── backtesting/                # NEW - Currency strength backtesting
│   └── indicators/                 # NEW - Advanced indicator processing
├── P_GUI/
│   ├── dashboard/                  # NEW - Dashboard GUI components
│   │   ├── tkinter_dashboard_gui.py
│   │   └── widgets/
│   ├── indicators/                 # NEW - Currency strength indicators
│   │   └── currency_strength/
│   └── testing/                    # NEW - Manual testing tools
│       └── control_panel.py
├── tests/
│   ├── integration/                # NEW - End-to-end testing
│   │   ├── signal_flow_tester.py
│   │   └── comprehensive_tests.py
│   └── fixtures/                   # NEW - Test data generators
│       ├── calendar_simulator.py
│       └── indicator_simulator.py
└── docs/
    ├── integration/                # NEW - Integration guides
    └── testing/                    # NEW - Testing documentation
```

## Configuration Updates

### Environment Variables
```bash
# Dashboard Configuration
DASHBOARD_UPDATE_INTERVAL=2
DASHBOARD_MAX_SIGNALS=500
DASHBOARD_DATABASE_PATH=data/dashboard.db

# Currency Strength Configuration
CURRENCY_STRENGTH_TIMEFRAMES=M1,M5,M15,M30,H1,H4,D1
CURRENCY_STRENGTH_PAIRS=EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD

# Testing Configuration
TEST_MT4_DATA_PATH=tests/data/mt4
TEST_TIMEOUT_SECONDS=300
```

### Makefile Updates
```makefile
# Add new test targets
test-signals:
	python tests/integration/signal_flow_tester.py --mt4-data tests/data/mt4

test-calendar:
	python tests/fixtures/calendar_simulator.py

test-dashboard:
	python tests/integration/dashboard_tests.py

# Add service management
start-dashboard:
	cd services/dashboard && python -m src.main

start-indicators:
	cd services/indicators && python -m src.main
```

## Risk Mitigation

### Testing Strategy
- **Unit Tests**: Each new component has comprehensive unit tests
- **Integration Tests**: End-to-end signal flow validation
- **Performance Tests**: Load testing with 500+ signals
- **Regression Tests**: Ensure existing functionality remains intact

### Rollback Plan
- **Incremental Deployment**: Deploy one phase at a time
- **Feature Flags**: Ability to disable new features if issues arise
- **Database Migrations**: Reversible schema changes
- **Configuration Rollback**: Previous configurations preserved

### Monitoring
- **Health Checks**: New services integrate with existing observability
- **Metrics**: Dashboard performance and signal processing metrics
- **Alerting**: Circuit breakers and error thresholds
- **Logging**: Comprehensive logging for troubleshooting

## Success Criteria

### Phase 1 Success (Testing)
- [ ] All existing tests continue to pass
- [ ] New testing framework validates signal flow end-to-end
- [ ] Manual testing control panel operational
- [ ] CI/CD pipeline enhanced with new test capabilities

### Phase 2 Success (Calendar)
- [ ] Automated ForexFactory downloads working
- [ ] Calendar events processed and exported correctly
- [ ] Error recovery and circuit breakers functional
- [ ] Emergency stop/resume controls operational

### Phase 3 Success (Currency Strength)
- [ ] Currency strength calculations accurate
- [ ] PyQt6 dashboard displays real-time data
- [ ] Multi-timeframe analysis working
- [ ] Backtesting framework produces valid results

### Phase 4 Success (Dashboard)
- [ ] Dashboard handles 500+ signals without performance degradation
- [ ] Real-time updates working at 2-second intervals
- [ ] Plugin architecture allows easy indicator addition
- [ ] Integration with existing DDE feeds successful

## Timeline

| Phase | Duration | Dependencies | Deliverables |
|-------|----------|--------------|--------------|
| Phase 1 | 2-3 days | None | Enhanced testing framework |
| Phase 2 | 3-4 days | Phase 1 | Automated calendar system |
| Phase 3 | 4-5 days | Phase 1 | Currency strength indicators |
| Phase 4 | 5-6 days | Phases 1-3 | Scalable dashboard system |

**Total Estimated Duration**: 14-18 days

## Next Steps

1. **Validate Current System**: Ensure all existing functionality works
2. **Begin Phase 1**: Integrate testing framework
3. **Setup Development Environment**: Prepare directories and dependencies
4. **Create Feature Branches**: One branch per phase for controlled integration
5. **Start Integration**: Begin systematic integration following this plan

---

**Document Version**: 1.0
**Last Updated**: 2025-09-20
**Status**: Planning Complete - Ready for Implementation