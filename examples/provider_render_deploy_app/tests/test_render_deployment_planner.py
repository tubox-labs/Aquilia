from examples.provider_render_deploy_app.modules.deployments.services import RenderDeploymentPlanner


def test_render_deployment_dry_run_builds_service_payload():
    planner = RenderDeploymentPlanner()
    plan = planner.dry_run({"AQ_ENV": "prod", "PORT": "8000"})

    assert plan["success"] is True
    assert plan["service_name"] == "provider-render-deploy-app"
    assert plan["payload"]["type"] == "web_service"
    assert {"key": "AQ_ENV", "value": "prod"} in plan["payload"]["serviceDetails"]["envVars"]
