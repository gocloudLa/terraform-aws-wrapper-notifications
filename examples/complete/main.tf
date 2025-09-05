module "wrapper_notifications" {
  source = "../../"

  metadata = local.metadata

  notifications_parameters = {
    enable = true

    # DISCORD
    notifications_discord_webhook_url = ""
    alarms_discord_webhook_url        = ""

    # TEAMS
    notifications_teams_webhook_url = ""
    alarms_teams_webhook_url        = ""

    # sns_topic_arn = ""
  }

  notifications_defaults = var.notifications_defaults
}