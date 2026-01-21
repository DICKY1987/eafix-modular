#!/bin/bash
# doc_id: DOC-INFRA-0006
# Container Image Digest Validation Script
# Enforces digest pinning policy for all Docker images

set -euo pipefail

EXIT_CODE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🔍 Validating Docker image digest pinning policy..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check Dockerfiles
check_dockerfiles() {
    local violations=()
    
    echo -e "${BLUE}Checking Dockerfiles for digest pinning...${NC}"
    
    while IFS= read -r -d '' dockerfile; do
        echo "  Checking: $dockerfile"
        
        # Check for FROM statements without digest
        if grep -n "^FROM.*:[^@]*$" "$dockerfile"; then
            violations+=("$dockerfile: FROM statement without SHA256 digest")
            EXIT_CODE=1
        fi
        
        # Check for latest tags (explicitly prohibited)
        if grep -n "FROM.*:latest" "$dockerfile"; then
            violations+=("$dockerfile: Uses prohibited 'latest' tag")
            EXIT_CODE=1
        fi
        
        # Check for floating version tags without digest
        if grep -nE "FROM.*:[0-9]+(\.[0-9]+)*[^@]*$" "$dockerfile"; then
            violations+=("$dockerfile: Floating version tag without digest")
            EXIT_CODE=1
        fi
        
    done < <(find "$REPO_ROOT" -name "Dockerfile" -print0)
    
    if [ ${#violations[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅ All Dockerfiles use proper digest pinning${NC}"
    else
        echo -e "  ${RED}❌ Dockerfile violations found:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "    ${RED}- $violation${NC}"
        done
    fi
}

# Function to check Docker Compose files
check_compose_files() {
    local violations=()
    
    echo -e "${BLUE}Checking Docker Compose files for digest pinning...${NC}"
    
    while IFS= read -r -d '' composefile; do
        echo "  Checking: $composefile"
        
        # Check for image statements without digest
        if grep -n "image:.*:[^@]*$" "$composefile"; then
            violations+=("$composefile: Image without SHA256 digest")
            EXIT_CODE=1
        fi
        
        # Check for latest tags
        if grep -n "image:.*:latest" "$composefile"; then
            violations+=("$composefile: Uses prohibited 'latest' tag")
            EXIT_CODE=1
        fi
        
        # Special exception for build contexts (these don't need digests)
        if grep -q "build:" "$composefile"; then
            echo "    ℹ️  Build context detected - skipping digest check for built images"
        fi
        
    done < <(find "$REPO_ROOT" -name "docker-compose*.yml" -print0)
    
    if [ ${#violations[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅ All Docker Compose files use proper digest pinning${NC}"
    else
        echo -e "  ${RED}❌ Docker Compose violations found:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "    ${RED}- $violation${NC}"
        done
    fi
}

# Function to check GitHub Actions workflows
check_github_actions() {
    local violations=()
    
    echo -e "${BLUE}Checking GitHub Actions workflows for digest pinning...${NC}"
    
    while IFS= read -r -d '' workflow; do
        echo "  Checking: $workflow"
        
        # Check for uses: docker:// without digest
        if grep -n "uses: docker://.*:[^@]*$" "$workflow"; then
            violations+=("$workflow: Docker action without SHA256 digest")
            EXIT_CODE=1
        fi
        
        # Check for container: without digest in job definitions
        if grep -n "container:.*:[^@]*$" "$workflow"; then
            violations+=("$workflow: Container image without SHA256 digest")
            EXIT_CODE=1
        fi
        
        # Check for latest tags in workflows
        if grep -n ":latest" "$workflow"; then
            violations+=("$workflow: Uses prohibited 'latest' tag")
            EXIT_CODE=1
        fi
        
    done < <(find "$REPO_ROOT/.github/workflows" -name "*.yml" -print0 2>/dev/null || true)
    
    if [ ${#violations[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅ All GitHub Actions workflows use proper digest pinning${NC}"
    else
        echo -e "  ${RED}❌ GitHub Actions violations found:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "    ${RED}- $violation${NC}"
        done
    fi
}

# Function to validate digest format
validate_digest_format() {
    local violations=()
    
    echo -e "${BLUE}Validating SHA256 digest format...${NC}"
    
    # Check all files for malformed digests
    while IFS= read -r -d '' file; do
        # Look for @sha256: patterns and validate them
        while IFS= read -r line_num line_content; do
            if [[ $line_content =~ @sha256:([a-f0-9]+) ]]; then
                local digest="${BASH_REMATCH[1]}"
                if [ ${#digest} -ne 64 ]; then
                    violations+=("$file:$line_num: Invalid SHA256 digest length (expected 64 chars, got ${#digest})")
                    EXIT_CODE=1
                fi
                if [[ ! $digest =~ ^[a-f0-9]+$ ]]; then
                    violations+=("$file:$line_num: Invalid SHA256 digest format (contains non-hex characters)")
                    EXIT_CODE=1
                fi
            fi
        done < <(grep -n "@sha256:" "$file" 2>/dev/null | head -20)
    done < <(find "$REPO_ROOT" \( -name "Dockerfile" -o -name "docker-compose*.yml" -o -path "*/.github/workflows/*.yml" \) -print0)
    
    if [ ${#violations[@]} -eq 0 ]; then
        echo -e "  ${GREEN}✅ All SHA256 digests have correct format${NC}"
    else
        echo -e "  ${RED}❌ Digest format violations found:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "    ${RED}- $violation${NC}"
        done
    fi
}

# Function to generate helpful suggestions
generate_suggestions() {
    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}🛠️  How to fix digest pinning violations:${NC}"
        echo ""
        echo "1. Get image digest:"
        echo "   docker inspect --format='{{index .RepoDigests 0}}' IMAGE:TAG"
        echo ""
        echo "2. Update Dockerfile:"
        echo "   FROM python:3.11-slim@sha256:abcd1234..."
        echo ""
        echo "3. Update Docker Compose:"
        echo "   image: redis:7-alpine@sha256:efgh5678..."
        echo ""
        echo "4. For GitHub Actions:"
        echo "   uses: docker://image:tag@sha256:ijkl9012..."
        echo ""
        echo -e "${BLUE}📖 See docs/security/image-digest-policy.md for complete policy${NC}"
    fi
}

# Main execution
main() {
    echo "Repository: $REPO_ROOT"
    echo ""
    
    check_dockerfiles
    echo ""
    
    check_compose_files
    echo ""
    
    check_github_actions
    echo ""
    
    validate_digest_format
    echo ""
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}🎉 All Docker images properly pinned with SHA256 digests!${NC}"
    else
        echo -e "${RED}💥 Digest pinning policy violations detected!${NC}"
        generate_suggestions
    fi
    
    exit $EXIT_CODE
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi