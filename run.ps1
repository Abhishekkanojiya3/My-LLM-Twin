# PowerShell script to replace Makefile commands on Windows
# Usage: .\run.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "`nAvailable commands:" -ForegroundColor Green
    Write-Host "  install                          - Create a local Poetry virtual environment and install dependencies"
    Write-Host "  install-superlinked              - Install with Superlinked enabled"
    Write-Host "  local-start                      - Start local Docker infrastructure"
    Write-Host "  local-build                      - Build local Docker infrastructure"
    Write-Host "  local-stop                       - Stop local Docker infrastructure"
    Write-Host "  local-test-medium                - Test crawling a Medium article"
    Write-Host "  local-test-github                - Test crawling a Github repository"
    Write-Host "  local-ingest-data                - Ingest all links from data/links.txt"
    Write-Host "  local-test-retriever             - Test the RAG retriever"
    Write-Host "  local-generate-instruct-dataset  - Generate fine-tuning instruct dataset"
    Write-Host "  download-instruct-dataset        - Download fine-tuning instruct dataset"
    Write-Host "  create-sagemaker-execution-role  - Create AWS SageMaker execution role"
    Write-Host "  start-training-pipeline          - Start training pipeline in AWS SageMaker"
    Write-Host "  start-training-pipeline-dummy    - Start training pipeline in dummy mode"
    Write-Host "  local-start-training-pipeline    - Start training pipeline locally"
    Write-Host "  deploy-inference-pipeline        - Deploy inference pipeline to AWS SageMaker"
    Write-Host "  call-inference-pipeline          - Call the inference pipeline"
    Write-Host "  delete-inference-pipeline        - Delete AWS SageMaker inference pipeline"
    Write-Host "  local-start-ui                   - Start Gradio UI for chatting with LLM Twin"
    Write-Host "  evaluate-llm                     - Run LLM evaluation tests"
    Write-Host "  evaluate-rag                     - Run RAG evaluation tests"
    Write-Host "  evaluate-llm-monitoring          - Run LLM monitoring evaluation"
    Write-Host "  local-start-superlinked          - Start Superlinked infrastructure"
    Write-Host "  local-stop-superlinked           - Stop Superlinked infrastructure"
    Write-Host "  test-superlinked-server          - Test Superlinked server"
    Write-Host "  local-bytewax-superlinked        - Run Bytewax streaming pipeline"
    Write-Host "  local-test-retriever-superlinked - Test Superlinked retriever"
    Write-Host ""
}

switch ($Command) {
    "help" {
        Show-Help
    }
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Cyan
        poetry env use 3.11
        poetry install --without superlinked_rag
    }
    "install-superlinked" {
        Write-Host "Installing dependencies with Superlinked..." -ForegroundColor Cyan
        poetry env use 3.11
        poetry install
    }
    "local-start" {
        Write-Host "Starting local Docker infrastructure..." -ForegroundColor Cyan
        docker compose -f docker-compose.yml up -d
    }
    "local-build" {
        Write-Host "Building local Docker infrastructure..." -ForegroundColor Cyan
        docker compose -f docker-compose.yml build
    }
    "local-stop" {
        Write-Host "Stopping local Docker infrastructure..." -ForegroundColor Cyan
        docker compose -f docker-compose.yml down --remove-orphans
    }
    "local-test-medium" {
        Write-Host "Testing Medium crawler..." -ForegroundColor Cyan
        $body = @{
            user = "Abhishek Kanojiya"
            link = "https://medium.com/decodingml/an-end-to-end-framework-for-production-ready-llm-systems-by-building-your-llm-twin-2cc6bb01141f"
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "http://localhost:9010/2015-03-31/functions/function/invocations" -Method Post -Body $body -ContentType "application/json"
    }
    "local-test-github" {
        Write-Host "Testing GitHub crawler..." -ForegroundColor Cyan
        $body = @{
            user = "Abhishek Kanojiya"
            link = "https://github.com/decodingml/llm-twin-course"
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "http://localhost:9010/2015-03-31/functions/function/invocations" -Method Post -Body $body -ContentType "application/json"
    }
    "local-ingest-data" {
        Write-Host "Ingesting data from links.txt..." -ForegroundColor Cyan
        Get-Content data/links.txt | ForEach-Object {
            $link = $_.Trim()
            if ($link) {
                Write-Host "Processing: $link"
                $body = @{
                    user = "Abhishek Kanojiya"
                    link = $link
                } | ConvertTo-Json
                Invoke-RestMethod -Uri "http://localhost:9010/2015-03-31/functions/function/invocations" -Method Post -Body $body -ContentType "application/json"
                Start-Sleep -Seconds 2
            }
        }
    }
    "local-test-retriever" {
        Write-Host "Testing RAG retriever..." -ForegroundColor Cyan
        Set-Location src/feature_pipeline
        poetry run python -m retriever
        Set-Location ../..
    }
    "local-generate-instruct-dataset" {
        Write-Host "Generating instruct dataset..." -ForegroundColor Cyan
        Set-Location src/feature_pipeline
        poetry run python -m generate_dataset.generate
        Set-Location ../..
    }
    "download-instruct-dataset" {
        Write-Host "Downloading instruct dataset..." -ForegroundColor Cyan
        Set-Location src/training_pipeline
        $env:PYTHONPATH = "$PWD\..\src"
        poetry run python download_dataset.py
        Set-Location ../..
    }
    "create-sagemaker-execution-role" {
        Write-Host "Creating SageMaker execution role..." -ForegroundColor Cyan
        Set-Location src
        $env:PYTHONPATH = $PWD
        poetry run python -m core.aws.create_execution_role
        Set-Location ..
    }
    "start-training-pipeline-dummy" {
        Write-Host "Starting training pipeline (dummy mode)..." -ForegroundColor Cyan
        Set-Location src/training_pipeline
        poetry run python run_on_sagemaker.py --is-dummy
        Set-Location ../..
    }
    "start-training-pipeline" {
        Write-Host "Starting training pipeline..." -ForegroundColor Cyan
        Set-Location src/training_pipeline
        poetry run python run_on_sagemaker.py
        Set-Location ../..
    }
    "local-start-training-pipeline" {
        Write-Host "Starting local training pipeline..." -ForegroundColor Cyan
        Set-Location src/training_pipeline
        poetry run python -m finetune
        Set-Location ../..
    }
    "deploy-inference-pipeline" {
        Write-Host "Deploying inference pipeline..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m aws.deploy_sagemaker_endpoint
        Set-Location ../..
    }
    "call-inference-pipeline" {
        Write-Host "Calling inference pipeline..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m main
        Set-Location ../..
    }
    "delete-inference-pipeline" {
        Write-Host "Deleting inference pipeline..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        $env:PYTHONPATH = "$PWD\..\src"
        poetry run python -m aws.delete_sagemaker_endpoint
        Set-Location ../..
    }
    "local-start-ui" {
        Write-Host "Starting Gradio UI..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m ui
        Set-Location ../..
    }
    "evaluate-llm" {
        Write-Host "Evaluating LLM..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m evaluation.evaluate
        Set-Location ../..
    }
    "evaluate-rag" {
        Write-Host "Evaluating RAG..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m evaluation.evaluate_rag
        Set-Location ../..
    }
    "evaluate-llm-monitoring" {
        Write-Host "Evaluating LLM monitoring..." -ForegroundColor Cyan
        Set-Location src/inference_pipeline
        poetry run python -m evaluation.evaluate_monitoring
        Set-Location ../..
    }
    "local-start-superlinked" {
        Write-Host "Starting Superlinked infrastructure..." -ForegroundColor Cyan
        docker compose -f docker-compose-superlinked.yml up --build -d
    }
    "local-stop-superlinked" {
        Write-Host "Stopping Superlinked infrastructure..." -ForegroundColor Cyan
        docker compose -f docker-compose-superlinked.yml down --remove-orphans
    }
    "test-superlinked-server" {
        Write-Host "Testing Superlinked server..." -ForegroundColor Cyan
        poetry run python src/bonus_superlinked_rag/local_test.py
    }
    "local-bytewax-superlinked" {
        Write-Host "Running Bytewax streaming pipeline..." -ForegroundColor Cyan
        $env:RUST_BACKTRACE = "full"
        poetry run python -m bytewax.run src/bonus_superlinked_rag/main.py
    }
    "local-test-retriever-superlinked" {
        Write-Host "Testing Superlinked retriever..." -ForegroundColor Cyan
        docker exec -it llm-twin-bytewax-superlinked python -m retriever
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}
