#!/usr/bin/env bash
# Performance test runner for ApexGraphSwarm
# Usage: ./run-tests.sh [test-type] [tool]
# Example: ./run-tests.sh load k6

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="${1:-all}"
TOOL="${2:-all}"
BASE_URL="${BASE_URL:-http://127.0.0.1:3010}"
TARGET_RPS="${TARGET_RPS:-10000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
INTEGRATION_TOKEN="${INTEGRATION_TOKEN:-}"

# Export environment variables
export BASE_URL
export TARGET_RPS
export AUTH_TOKEN
export INTEGRATION_TOKEN

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if target is reachable
    if ! curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/integrations" | grep -q "200"; then
        log_error "Target ${BASE_URL} is not reachable. Please start the server first."
        exit 1
    fi

    # Check k6
    if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
        if ! command -v k6 &> /dev/null; then
            log_warning "k6 is not installed. Install with: brew install k6"
            if [[ "${TOOL}" == "k6" ]]; then
                exit 1
            fi
        else
            log_success "k6 found: $(k6 version)"
        fi
    fi

    # Check artillery
    if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
        if ! command -v artillery &> /dev/null; then
            log_warning "artillery is not installed. Install with: npm install -g artillery"
            if [[ "${TOOL}" == "artillery" ]]; then
                exit 1
            fi
        else
            log_success "artillery found: $(artillery --version)"
        fi
    fi
}

run_k6_test() {
    local test_name=$1
    local test_file=$2

    log_info "Running k6 ${test_name} test..."
    log_info "Target: ${BASE_URL}"
    log_info "Target RPS: ${TARGET_RPS}"

    if k6 run \
        --out json="${SCRIPT_DIR}/results/k6-${test_name}-$(date +%Y%m%d-%H%M%S).json" \
        "${SCRIPT_DIR}/k6/${test_file}"; then
        log_success "k6 ${test_name} test completed"
    else
        log_error "k6 ${test_name} test failed"
        return 1
    fi
}

run_artillery_test() {
    local test_name=$1
    local test_file=$2

    log_info "Running Artillery ${test_name} test..."
    log_info "Target: ${BASE_URL}"
    log_info "Target RPS: ${TARGET_RPS}"

    if artillery run \
        --output "${SCRIPT_DIR}/results/artillery-${test_name}-$(date +%Y%m%d-%H%M%S).json" \
        "${SCRIPT_DIR}/artillery/${test_file}"; then
        log_success "Artillery ${test_name} test completed"
    else
        log_error "Artillery ${test_name} test failed"
        return 1
    fi
}

run_tests() {
    mkdir -p "${SCRIPT_DIR}/results"

    case "${TEST_TYPE}" in
        load)
            if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
                run_k6_test "load" "load-test.js"
            fi
            if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
                run_artillery_test "load" "load-test.yml"
            fi
            ;;
        stress)
            if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
                run_k6_test "stress" "stress-test.js"
            fi
            if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
                run_artillery_test "stress" "stress-test.yml"
            fi
            ;;
        spike)
            if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
                run_k6_test "spike" "spike-test.js"
            fi
            if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
                run_artillery_test "spike" "spike-test.yml"
            fi
            ;;
        endurance)
            if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
                run_k6_test "endurance" "endurance-test.js"
            fi
            if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
                run_artillery_test "endurance" "endurance-test.yml"
            fi
            ;;
        all)
            log_info "Running all performance tests..."
            run_tests_by_type "load"
            run_tests_by_type "stress"
            run_tests_by_type "spike"
            run_tests_by_type "endurance"
            ;;
        *)
            log_error "Unknown test type: ${TEST_TYPE}"
            echo "Usage: $0 [load|stress|spike|endurance|all] [k6|artillery|all]"
            exit 1
            ;;
    esac
}

run_tests_by_type() {
    local test_type=$1
    if [[ "${TOOL}" == "k6" || "${TOOL}" == "all" ]]; then
        run_k6_test "${test_type}" "${test_type}-test.js"
    fi
    if [[ "${TOOL}" == "artillery" || "${TOOL}" == "all" ]]; then
        run_artillery_test "${test_type}" "${test_type}-test.yml"
    fi
}

# Main execution
main() {
    echo "========================================"
    echo "ApexGraphSwarm Performance Test Suite"
    echo "========================================"
    echo "Test Type: ${TEST_TYPE}"
    echo "Tool: ${TOOL}"
    echo "Target: ${BASE_URL}"
    echo "Target RPS: ${TARGET_RPS}"
    echo "========================================"
    echo ""

    check_prerequisites
    run_tests

    echo ""
    log_success "All tests completed!"
    echo "Results saved to: ${SCRIPT_DIR}/results/"
}

main "$@"
