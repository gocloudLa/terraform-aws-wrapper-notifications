/*----------------------------------------------------------------------*/
/* Common |                                                             */
/*----------------------------------------------------------------------*/

variable "metadata" {
  type = any
}

/*----------------------------------------------------------------------*/
/* Notifications | Variable Definition                                  */
/*----------------------------------------------------------------------*/
variable "notifications_parameters" {
  type        = any
  description = "Notifications parameteres"
  default     = {}
}

variable "notifications_defaults" {
  type        = any
  description = "Notifications default parameteres"
  default     = {}
}