import { Component } from '@angular/core';
import { ChatUiComponent } from '../../../shared/components/chat-ui/chat-ui.component';

@Component({
  selector: 'app-analyst-chat',
  standalone: true,
  imports: [ChatUiComponent],
  template: `<app-chat-ui mode="analyst"></app-chat-ui>`,
  styleUrl: './analyst-chat.component.css'
})
export class AnalystChatComponent {

}
