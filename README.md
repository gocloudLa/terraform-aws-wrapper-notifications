# Standard Platform - Terraform Module 🚀🚀
<p align="right"><a href="https://partners.amazonaws.com/partners/0018a00001hHve4AAC/GoCloud"><img src="https://img.shields.io/badge/AWS%20Partner-Advanced-orange?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS Partner"/></a><a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge&logo=apache&logoColor=white" alt="LICENSE"/></a></p>

Welcome to the Standard Platform — a suite of reusable and production-ready Terraform modules purpose-built for AWS environments.
Each module encapsulates best practices, security configurations, and sensible defaults to simplify and standardize infrastructure provisioning across projects.

## 📦 Module: Terraform Cloudwatch Notifications Module
<p align="right"><a href="https://github.com/gocloudLa/terraform-aws-wrapper-notifications/releases/latest"><img src="https://img.shields.io/github/v/release/gocloudLa/terraform-aws-wrapper-notifications.svg?style=for-the-badge" alt="Latest Release"/></a><a href=""><img src="https://img.shields.io/github/last-commit/gocloudLa/terraform-aws-wrapper-notifications.svg?style=for-the-badge" alt="Last Commit"/></a><a href="https://registry.terraform.io/modules/gocloudLa/wrapper-notifications/aws"><img src="https://img.shields.io/badge/Terraform-Registry-7B42BC?style=for-the-badge&logo=terraform&logoColor=white" alt="Terraform Registry"/></a></p>
The Terraform Wrapper for Notifications provides the implementation of two lambdas to handle different types of notifications via Discord and/or Teams.

### ✨ Features

- 📋 [Log Notifications](#log-notifications) - Receives events from CloudWatch subscription filter and sends formatted log messages

- 🚨 [Alarm Notifications](#alarm-notifications) - Receives CloudWatch alarms and various AWS events, then sends formatted notifications



### 🔗 External Modules
| Name | Version |
|------|------:|
| <a href="https://github.com/terraform-aws-modules/terraform-aws-lambda" target="_blank">terraform-aws-modules/lambda/aws</a> | 8.1.2 |



## 🚀 Quick Start
```hcl
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
```


## 🔧 Additional Features Usage

### Log Notifications
Processes CloudWatch log events received via subscription filters and sends formatted notifications to Discord and/or Teams channels. 
Supports both JSON structured logs and plain text logs with automatic parsing and color-coded severity levels (ERROR, WARN, DEBUG, INFO).
Extracts additional metadata like source files and stack traces when available.


<details><summary>Configuration Code</summary>

```hcl
module "notifications" {
  source = "gocloudLa/wrapper-notifications/aws"
  
  notifications_parameters = {
    enable = true
    
    # Discord webhook for log notifications
    notifications_discord_webhook_url = var.notifications_discord_webhook_url
    
    # Teams webhook for log notifications  
    notifications_teams_webhook_url = var.notifications_teams_webhook_url
  }
}
```


</details>


### Alarm Notifications
Processes multiple types of AWS events and sends formatted notifications to Discord and/or Teams:
- **CloudWatch Alarms**: Processes alarm state changes with custom tags and metadata
- **EventBridge Events**: Handles ECS task state changes and AWS Health events
- **Budget Alerts**: Processes AWS Budget notifications with spending thresholds
- **SES Events**: Handles email bounce, complaint, and delivery notifications
- **Unknown Events**: Gracefully handles unrecognized event formats


<details><summary>Configuration Code</summary>

```hcl
module "notifications" {
  source = "gocloudLa/wrapper-notifications/aws"
  
  notifications_parameters = {
    enable = true
    
    # Discord webhook for alarm notifications
    alarms_discord_webhook_url = var.alarms_discord_webhook_url
    
    # Teams webhook for alarm notifications
    alarms_teams_webhook_url = var.alarms_teams_webhook_url
    
    # Optional: Use existing SNS topic
    sns_topic_arn = var.sns_topic_arn
  }
}
```


</details>




## 📑 Inputs
| Name                              | Description                                       | Type     | Default  | Required |
| --------------------------------- | ------------------------------------------------- | -------- | -------- | -------- |
| enable                            | Controls the creation of services                 | `bool`   | `"true"` | no       |
| notifications_discord_webhook_url | Discord Webhook endpoint for log notifications    | `string` | `""`     | no       |
| alarms_discord_webhook_url        | Discord Webhook endpoint for alarm notifications  | `string` | `""`     | no       |
| notifications_teams_webhook_url   | Teams Webhook endpoint for log notifications      | `string` | `""`     | no       |
| alarms_teams_webhook_url          | Teams Webhook endpoint for alarm notifications    | `string` | `""`     | no       |
| sns_topic_arn                     | ARN of an existing SNS Topic for sending messages | `string` | `""`     | no       |
| tags                              | A map of tags to assign to resources.             | `map`    | `{}`     | no       |








---

## 🤝 Contributing
We welcome contributions! Please see our contributing guidelines for more details.

## 🆘 Support
- 📧 **Email**: info@gocloud.la

## 🧑‍💻 About
We are focused on Cloud Engineering, DevOps, and Infrastructure as Code.
We specialize in helping companies design, implement, and operate secure and scalable cloud-native platforms.
- 🌎 [www.gocloud.la](https://www.gocloud.la)
- ☁️ AWS Advanced Partner (Terraform, DevOps, GenAI)
- 📫 Contact: info@gocloud.la

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details. 